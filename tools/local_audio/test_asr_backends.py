"""CPU adapter and encoding/cache behavior, without claiming Windows execution."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import asr_backends as cpu
import localize


class CPUBackendTests(unittest.TestCase):
    def test_cli_json_succeeds_with_unicode_paths_in_cp1252_stdout(self):
        import io,sys
        with tempfile.TemporaryDirectory(prefix='中文 空格 ') as directory:
            root=Path(directory);audio=root/'本集.wav';audio.write_bytes(b'fixture')
            script=root/'剧本.json';localize.save(script,{'units':[{'id':'n','text':'Stay.','kind':'narration','speaker':'narrator'}]})
            transcript={'text':'Stay.','segments':[{'words':[{'word':'Stay.','start':0,'end':1}]}]}
            raw=io.BytesIO();stream=io.TextIOWrapper(raw,encoding='cp1252',errors='strict')
            argv=['localize.py','--audio',str(audio),'--script',str(script),'--out',str(root/'输出')]
            with patch.object(sys,'argv',argv),patch.object(sys,'stdout',stream),patch.object(localize,'decode',return_value=(b'\0\0'*32000,'fixture')),patch.object(localize,'get_transcript',return_value=(transcript,{'transcript_cache_hit':True})):
                localize.main();stream.flush()
            report=json.loads(raw.getvalue().decode('ascii'))
            self.assertIn('输出',report['result_path'])
            self.assertFalse(report['automatic_pass'])

    def test_platform_routes_and_unsupported_arch(self):
        self.assertEqual(cpu.select_backend(system='Windows',machine='AMD64'),'faster-whisper')
        self.assertEqual(cpu.select_backend(system='Darwin',machine='arm64'),'mlx')
        with self.assertRaises(ValueError):cpu.select_backend(system='Windows',machine='ARM64')

    def test_lazy_words_keep_timeline_text_and_probability(self):
        s=NS(id=0,start=1.5,end=2.4,text=' Stay here.',words=[NS(word=' Stay',start=1.5,end=2,probability=.9),NS(word=' here.',start=2,end=2.4,probability=.8)])
        result=cpu.normalize_segments(iter([s]),NS(language='en'))
        localize.validate_transcript(result,3)
        self.assertEqual(result['segments'][0]['words'][0]['start'],1.5)
        self.assertEqual(result['text'],' Stay here.')
        self.assertEqual(result['segments'][0]['words'][-1]['word'],' here.')
        with self.assertRaises(ValueError):cpu.normalize_segments([NS(words=None)],NS(language='en'))

    def test_cpu_cache_hit_imports_no_asr_runtime_and_tampering_rejected(self):
        pcm=b'\0\0'*32000
        result={'text':' Stay.','language':'en','segments':[{'words':[{'word':' Stay.','start':.2,'end':.8,'probability':.9}]}]}
        with tempfile.TemporaryDirectory(prefix='中文 空格 ') as directory:
            root=Path(directory); settings=cpu.settings(localize.digest(pcm),{})
            key=localize.digest(json.dumps(settings,sort_keys=True).encode('utf-8'))
            path=root/'transcripts'/(key+'.json')
            localize.save(path,dict(settings=settings,transcript=result,transcript_sha256=localize.transcript_sha(result)))
            with patch.object(cpu,'versions',return_value={}),patch.object(cpu,'transcribe',side_effect=AssertionError('no inference')),patch.object(cpu,'model_directory',side_effect=AssertionError('no download')):
                actual,timing=localize.get_transcript(pcm,root,backend='faster-whisper')
                self.assertEqual(actual,result);self.assertTrue(timing['transcript_cache_hit'])
                record=json.loads(path.read_text(encoding='utf-8'));record['transcript']['text']='changed';localize.save(path,record)
                with self.assertRaisesRegex(ValueError,'checksum'):cpu.get_transcript(pcm,root)

    def test_backend_model_compute_params_separate_cache_keys(self):
        original=cpu.settings('a'*64,{})
        keys=[]
        for field,value in [('backend','other'),('revision','new'),('runtime',dict(cpu.RUNTIME,compute_type='float32')),('parameters',dict(cpu.PARAMS,vad_filter=True))]:
            changed=copy.deepcopy(original);changed[field]=value
            self.assertNotEqual(localize.transcript_sha(original),localize.transcript_sha(changed))
            keys.append(localize.transcript_sha(changed))
        self.assertEqual(len(set(keys)),4)
        self.assertFalse(cpu.PARAMS['vad_filter'])

    def test_cpu_model_offline_manifest_reuse_and_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);model=root/'models/faster-whisper-small-en';model.mkdir(parents=True)
            for name in cpu.FILES:(model/name).write_bytes(name.encode())
            localize.save(model/'local_manifest.json',dict(backend='faster-whisper',model=cpu.MODEL,revision=cpu.REVISION,files={n:localize.digest((model/n).read_bytes()) for n in cpu.FILES}))
            path,timing=cpu.model_directory(root)
            self.assertEqual(path,str(model));self.assertEqual(timing['model_download_seconds'],0)
            (model/'tokenizer.json').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'integrity'):cpu.model_directory(root)

    def test_backend_identity_changes_adoption_even_when_words_match(self):
        units=[dict(id='n',text='Stay.',kind='narration',speaker='narrator')]
        matched=localize.match_units(units,{'segments':[{'words':[{'word':'Stay.','start':0,'end':1}]}]})
        args=('a'*64,'b'*64,2,matched,[],[],[],[],{})
        legacy=localize.make_candidate(*args)
        new=localize.make_candidate(*args,transcription_identity=cpu.settings('b'*64,{}))
        changed=copy.deepcopy(new);changed['transcription_identity']['runtime']['compute_type']='float32'
        self.assertNotEqual(localize.audio_content_identity(legacy),localize.audio_content_identity(new))
        self.assertNotEqual(localize.audio_content_identity(new),localize.audio_content_identity(changed))

    def test_interrupted_model_download_resumes_without_success_manifest(self):
        import sys
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);model=root/'models/faster-whisper-small-en'
            def partial(*args,**kwargs):
                model.mkdir(parents=True,exist_ok=True);(model/'model.bin').write_bytes(b'partial')
                raise OSError('download interrupted')
            with patch.dict(sys.modules,{'huggingface_hub':NS(snapshot_download=partial)}):
                with self.assertRaises(OSError):cpu.model_directory(root)
            self.assertFalse((model/'local_manifest.json').exists())
            def completed(repo,revision,allow_patterns,local_dir):
                self.assertEqual(revision,cpu.REVISION)
                for name in cpu.FILES:(model/name).write_bytes(name.encode())
            with patch.dict(sys.modules,{'huggingface_hub':NS(snapshot_download=completed)}):
                _,timing=cpu.model_directory(root)
            self.assertTrue(timing['model_local_verified'])
            self.assertTrue((model/'local_manifest.json').is_file())

    def test_changed_mlx_revision_gets_new_candidate_identity(self):
        pcm=b'\0\0'*32000
        transcript={'text':' Stay.','segments':[{'words':[{'word':' Stay.','start':0,'end':1}]}]}
        with tempfile.TemporaryDirectory() as directory:
            cache=Path(directory)
            settings=dict(format_version=localize.VERSION,pcm_sha256=localize.digest(pcm),pcm_format='16000 Hz mono s16le',model=localize.MODEL,revision='new-revision',parameters=localize.PARAMS,tool_versions={})
            key=localize.digest(json.dumps(settings,sort_keys=True).encode())
            localize.save(cache/'transcripts'/(key+'.json'),dict(settings=settings,transcript=transcript,transcript_sha256=localize.transcript_sha(transcript)))
            with patch.object(localize,'REVISION','new-revision'),patch.object(localize,'configured_versions',return_value={}):
                _,timing=localize.get_transcript(pcm,cache,backend='mlx')
            self.assertEqual(timing['transcription_identity']['revision'],'new-revision')

    def test_utf8_and_file_occupied_preserves_old_payload(self):
        with tempfile.TemporaryDirectory(prefix='中文 路径 ') as directory:
            p=Path(directory)/'采用 记录.json';localize.save(p,{'text':'原句—身份'})
            before=p.read_bytes()
            with patch.object(Path,'replace',side_effect=PermissionError('file occupied')):
                with self.assertRaises(PermissionError):localize.save(p,{'text':'new'})
            self.assertEqual(p.read_bytes(),before)
            self.assertEqual(json.loads(before.decode('utf-8'))['text'],'原句—身份')


if __name__=='__main__':unittest.main()
