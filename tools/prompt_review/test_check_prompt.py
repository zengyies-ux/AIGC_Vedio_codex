import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from check_prompt import assess_episode_budget, inspect

def sample(shots=((0,2),(2,3.4),(3.4,5.6)), sound='局部1.0–5.0秒｜甲→乙｜“A complete sentence.”｜一次连续发声', prose=None):
    end=shots[-1][1]
    body=f'【生成任务】\n生成{end}秒，共{len(shots)}个真实镜头。\n【声音时序】\n{sound}\n【镜头设计】\n'
    for i,(a,b) in enumerate(shots,1):
        body+=f'镜头{i:02}【{a}–{b}秒｜紧特写】\n'+(prose or {}).get(i,'甲在画外持续发声，乙收回伸出的手。')+'\n'
    return '制作设置：原轨由后期编排。\n```text\n'+body+'```'

class PromptChecks(unittest.TestCase):
    def codes(self,text): return {x['code'] for x in inspect(text)['errors']}
    def test_continuous_speech_across_three_shots(self):
        self.assertTrue(inspect(sample())['structural_pass'])
        self.assertEqual(inspect(sample())['visual_quality'],'not_assessed')
    def test_long_shot_rejected(self):
        self.assertIn('shot_too_long',self.codes(sample(((0,5.6),))))
    def test_gap_rejected(self):
        self.assertIn('coverage_gap_or_overlap',self.codes(sample(((0,2),(2.1,3.4),(3.4,5.6)))))
    def test_overlap_rejected(self):
        self.assertIn('coverage_gap_or_overlap',self.codes(sample(((0,2),(1.9,3.4),(3.4,5.6)))))
    def test_opening_in_wrong_shot(self):
        self.assertIn('opening_outside_shot',self.codes(sample(prose={2:'现场对白：按声音时序1.0秒开口。'})))
    def test_legal_opening_and_offscreen_continuation(self):
        self.assertTrue(inspect(sample(prose={1:'现场对白：局部1.0秒开口。',2:'甲画外持续同句，乙安静听着。'}))['structural_pass'])
    def test_postproduction_in_body_not_settings(self):
        self.assertNotIn('postproduction_in_body',self.codes(sample()))
        self.assertIn('postproduction_in_body',self.codes(sample(prose={1:'P1092旁白由后期编排。'})))
    def test_hidden_cut_requires_review(self):
        r=inspect(sample(prose={1:'切到乙再回到甲。'}))
        self.assertIn('inspect_hidden_cut',{x['code'] for x in r['warnings']})
    def test_count_and_end(self):
        self.assertIn('shot_count',self.codes(sample().replace('共3个','共9个')))
        self.assertIn('end_coverage',self.codes(sample().replace('生成5.6秒','生成6秒')))
    def test_no_fake_point_eight_minimum(self):
        self.assertTrue(inspect(sample(((0,.6),(.6,3),(3,5.6))))['structural_pass'])
    def test_missing_body_fails_closed(self):
        self.assertFalse(inspect('只有摘要')['structural_pass'])
    def test_other_explicit_upper_limit(self):
        self.assertTrue(inspect(sample(((0,5.6),)),6)['structural_pass'])
    def test_missing_count_rejected(self):
        self.assertIn('shot_count_missing',self.codes(sample().replace('共3个真实镜头','若干镜头')))
    def test_short_count_form(self):
        self.assertTrue(inspect(sample().replace('共3个真实镜头','共3镜'))['structural_pass'])
    def test_invalid_limit(self):
        with self.assertRaises(ValueError): inspect(sample(),float('nan'))

class EpisodeBudgetChecks(unittest.TestCase):
    def budget(self, audio=70.1649375, total=78):
        return {'audio_seconds': audio,
                'segments': [{'path': '01.md', 'mode': 'native', 'seconds': total}]}

    def test_no_episode_information_is_not_assessed(self):
        self.assertEqual(assess_episode_budget()['detail'], 'budget not assessed')
        self.assertEqual(inspect(sample())['episode_budget']['status'], 'not_assessed')

    def test_all_required_integer_boundaries(self):
        cases = [(70, 76, True), (70, 80, True), (70, 75, False), (70, 81, False),
                 (70.1649375, 77, True), (70.1649375, 80, True),
                 (70.1649375, 76, False), (70.1649375, 81, False),
                 (70.1649375, 71, False), (70.1649375, 101, False)]
        for audio, total, expected in cases:
            with self.subTest(audio=audio, total=total):
                result = assess_episode_budget(self.budget(audio, total))
                self.assertEqual(result['budget_pass'], expected)
                self.assertEqual(result['integer_generated_range'], [76, 80] if audio == 70 else [77, 80])

    def test_native_plus_extension_counts_new_seconds_once(self):
        data = self.budget()
        data['segments'] = [{'path': '01.md', 'mode': 'native', 'seconds': 30},
                            {'path': '02.md', 'mode': 'extension', 'seconds': 20},
                            {'path': '03.md', 'mode': 'native', 'seconds': 28}]
        report = assess_episode_budget(data)
        self.assertEqual(report['generated_seconds'], 78)
        self.assertAlmostEqual(report['reserve_seconds'], 7.8350625)
        self.assertTrue(report['budget_pass'])

    def test_anonymous_allocation(self):
        data = self.budget()
        data['segments'] = [{'path': f'{i}.md', 'mode': 'native', 'seconds': n}
                            for i, n in enumerate([21, 15, 28, 15])]
        self.assertAlmostEqual(assess_episode_budget(data)['reserve_seconds'], 8.8350625)

    def test_duplicate_explicit_paths_rejected_including_aliases(self):
        for second in ['01.md', './01.md', 'sub/../01.md']:
            data = self.budget()
            data['segments'].append({'path': second, 'mode': 'extension', 'seconds': 1})
            with self.subTest(second=second), self.assertRaisesRegex(ValueError, 'duplicate'):
                assess_episode_budget(data)

    def test_invalid_seconds_mode_and_globs_rejected(self):
        for key, values in {'seconds': [0, -1, 2.5, 20.0, True, '20', float('nan')],
                            'mode': ['extend', '', None], 'path': ['', 'old/*.md']}.items():
            for value in values:
                data = self.budget()
                data['segments'][0][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    assess_episode_budget(data)

    def test_invalid_audio_rejected(self):
        for value in [0, -1, float('nan'), float('inf'), True, '70', None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                assess_episode_budget(self.budget(value))

    def test_no_retry_or_source_length_accounting(self):
        for key in ['source_seconds', 'failed_retry_seconds', 'attempts']:
            data = self.budget(total=71)
            data['segments'][0][key] = 30
            with self.subTest(key=key), self.assertRaises(ValueError):
                assess_episode_budget(data)
        # A failed attempt is not one of the explicit unique current segments.
        self.assertFalse(assess_episode_budget(self.budget(total=71))['budget_pass'])

    def test_incomplete_or_unknown_inputs_rejected(self):
        for value in [{}, {'audio_seconds': 70}, {'audio_seconds': 70, 'segments': []},
                      {'audio_seconds': 70, 'segments': [], 'history': '*.md'}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                assess_episode_budget(value)

    def test_cli_does_not_discover_or_count_history(self):
        script = Path(__file__).with_name('check_prompt.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # A=2 and one current eight-second segment: R=6; old file is ignored.
            (root / 'current.md').write_text(sample(((0, 2), (2, 4), (4, 6), (6, 8))))
            (root / 'old.md').write_text('not a current prompt')
            (root / 'budget.json').write_text(json.dumps(self.budget(2, 8)).replace('01.md', 'current.md'))
            result = subprocess.run([sys.executable, str(script), '--episode-budget', str(root / 'budget.json')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(len(output['prompts']), 1)
            self.assertEqual(output['episode_budget']['generated_seconds'], 8)
            result = subprocess.run([sys.executable, str(script), str(root / 'current.md')],
                                    capture_output=True, text=True)
            self.assertEqual(json.loads(result.stdout)[0]['episode_budget']['status'], 'not_assessed')
            result = subprocess.run([sys.executable, str(script), str(root / 'old.md'),
                                     '--episode-budget', str(root / 'budget.json')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('exactly match', result.stderr)
            (root / 'current.md').write_text(sample(((0, 2), (2, 4), (4, 6))))
            result = subprocess.run([sys.executable, str(script), '--episode-budget', str(root / 'budget.json')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            output = json.loads(result.stdout)
            self.assertIn('submission_duration_mismatch', {e['code'] for e in output['prompts'][0]['errors']})


class ExtensionSourceChecks(unittest.TestCase):
    def source(self, reference='@视频1', state_name='片段01源视频'):
        addition = ('【人物与场景参考】\n片段01源视频：【' + reference + '】\n'
                    '【空间与道具状态】\n' + state_name + '：延续源片实际站位和持物末态。\n')
        return sample().replace('【声音时序】', addition + '【声音时序】')

    def test_missing_video_reference_rejected_but_no_binding_claim(self):
        report = inspect(sample(), generation_mode='extension')
        self.assertFalse(report['structural_pass'])
        self.assertEqual(report['source_reference']['source_binding'], 'not_assessed')
        self.assertIn('extension_source_reference', {x['code'] for x in report['errors']})

    def test_source_name_must_match_state(self):
        report = inspect(self.source(state_name='片段00源视频'), generation_mode='extension')
        self.assertEqual(report['source_reference']['status'], 'state_name_missing')
        self.assertFalse(report['structural_pass'])

    def test_text_reference_never_certifies_real_binding(self):
        for reference in ['@视频1', '@视频2']:
            report = inspect(self.source(reference), generation_mode='extension')
            self.assertTrue(report['structural_pass'])
            self.assertEqual(report['source_reference']['status'], 'text_reference_present')
            self.assertEqual(report['source_reference']['video_reference'], reference)
            self.assertEqual(report['source_reference']['source_binding'], 'not_assessed')
            self.assertEqual(report['source_continuity'], 'not_assessed')
            self.assertEqual(report['visual_quality'], 'not_assessed')
        # No real node/source identity evidence: neither preset numbering can pass binding.
        text = self.source().replace('片段01源视频', '首段原生结果')
        report = inspect(text, generation_mode='extension')
        self.assertTrue(report['structural_pass'])
        self.assertEqual(report['source_reference']['source_name'], '首段原生结果')
        self.assertEqual(report['source_reference']['video_reference'], '@视频1')
        self.assertEqual(report['source_reference']['source_binding'], 'not_assessed')

    def test_missing_state_and_ambiguous_sources_rejected(self):
        text = self.source().replace('片段01源视频：延续源片实际站位和持物末态。', '')
        self.assertFalse(inspect(text, generation_mode='extension')['structural_pass'])
        text = self.source().replace('片段01源视频：延续源片实际站位和持物末态。', '片段01源视频：')
        self.assertFalse(inspect(text, generation_mode='extension')['structural_pass'])
        text = self.source().replace('片段01源视频：【@视频1】',
                                     '片段01源视频：【@视频1】\n片段03源视频：【@视频2】')
        self.assertEqual(inspect(text, generation_mode='extension')['source_reference']['status'],
                         'missing_or_ambiguous')

    def test_native_and_unspecified_modes_do_not_infer_extension(self):
        for mode in [None, 'native']:
            report = inspect(sample(), generation_mode=mode)
            self.assertTrue(report['structural_pass'])
            self.assertEqual(report['source_reference']['status'], 'not_assessed')
        with self.assertRaises(ValueError):
            inspect(sample(), generation_mode='invalid')

if __name__=='__main__': unittest.main()
