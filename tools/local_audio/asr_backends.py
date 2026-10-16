"""Pinned Windows CPU ASR adapter. No MLX import or system ffmpeg required."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import time

MODEL = 'Systran/faster-whisper-small.en'
REVISION = 'd1d751a5f8271d482d14ca55d9e2deeebbae577f'
FILES = ('config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt')
PARAMS = dict(language='en', task='transcribe', word_timestamps=True,
              temperature=0.0, condition_on_previous_text=True,
              beam_size=5, best_of=5, patience=1.0, vad_filter=False)
RUNTIME = dict(device='cpu', compute_type='int8', cpu_threads=4, num_workers=1)
PACKAGES = ('faster-whisper', 'ctranslate2', 'imageio-ffmpeg', 'numpy',
            'onnxruntime', 'tokenizers', 'huggingface-hub')


def select_backend(requested='auto', system=None, machine=None):
    if requested not in ('auto', 'mlx', 'faster-whisper'):
        raise ValueError('Unknown audio backend')
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    if requested != 'auto':
        return requested
    if system == 'Windows':
        if machine not in ('amd64', 'x86_64'):
            raise ValueError('Windows audio candidate supports x64 CPU only')
        return 'faster-whisper'
    if system == 'Darwin' and machine in ('arm64', 'aarch64'):
        return 'mlx'
    raise ValueError('No validated default audio backend for this platform; select a supported candidate explicitly')


def versions():
    return {name: importlib.metadata.version(name) for name in PACKAGES}


def settings(pcm_sha, tool_versions=None):
    return dict(format_version='windows-cpu-1', pcm_sha256=pcm_sha,
                pcm_format='16000 Hz mono s16le', backend='faster-whisper',
                model=MODEL, revision=REVISION, runtime=RUNTIME,
                parameters=PARAMS, tool_versions=versions() if tool_versions is None else tool_versions)


def model_directory(cache, protected=()):
    # Import only shared file helpers, never the platform's ASR runtime.
    from localize import save, ensure_no_collisions, digest
    model = Path(cache) / 'models' / 'faster-whisper-small-en'
    manifest = model / 'local_manifest.json'
    ensure_no_collisions([manifest, manifest.with_suffix('.json.tmp'),
                          *(model / n for n in FILES)], protected)
    started = time.perf_counter()
    if manifest.exists():
        record = json.loads(manifest.read_text(encoding='utf-8'))
        if (record.get('backend'), record.get('model'), record.get('revision')) != ('faster-whisper', MODEL, REVISION):
            raise ValueError('CPU model repo/revision mismatch; use a separate cache')
        for name in FILES:
            if not (model / name).is_file() or digest((model / name).read_bytes()) != record.get('files', {}).get(name):
                raise ValueError('CPU model integrity failed: ' + name)
        return str(model), dict(model_local_verified=True, model_download_seconds=0,
                               model_integrity_check_seconds=time.perf_counter()-started)
    from huggingface_hub import snapshot_download
    # Interrupted downloads leave no success manifest; HF resumes only missing data.
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    snapshot_download(MODEL, revision=REVISION, allow_patterns=list(FILES), local_dir=model)
    record = dict(backend='faster-whisper', model=MODEL, revision=REVISION,
                  files={n: digest((model / n).read_bytes()) for n in FILES})
    save(manifest, record, protected)
    return str(model), dict(model_local_verified=True, model_download_seconds=time.perf_counter()-started)


def normalize_segments(segments, info):
    """Retain full original timeline, words and probabilities in the existing schema."""
    rows = []
    for segment in segments:  # Consume lazy generator; do not report success before inference.
        if segment.words is None:
            raise ValueError('CPU ASR returned no word timestamps')
        rows.append(dict(id=segment.id, start=float(segment.start), end=float(segment.end),
                         text=segment.text, words=[dict(word=w.word, start=float(w.start),
                         end=float(w.end), probability=float(w.probability)) for w in segment.words]))
    return dict(text=''.join(s['text'] for s in rows), language=info.language, segments=rows)


def transcribe(pcm, model_path):
    import numpy as np
    from faster_whisper import WhisperModel
    signal = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    model = WhisperModel(str(model_path), local_files_only=True, **RUNTIME)
    segments, info = model.transcribe(signal, **PARAMS)
    return normalize_segments(segments, info)


def get_transcript(pcm, cache, force=False, protected=()):
    from localize import digest, transcript_sha, validate_transcript, ensure_no_collisions, save
    current = settings(digest(pcm))
    key = digest(json.dumps(current, sort_keys=True).encode('utf-8'))
    destination = Path(cache) / 'transcripts' / (key + '.json')
    ensure_no_collisions([destination, destination.with_suffix('.json.tmp')], protected)
    started = time.perf_counter()
    if destination.exists() and not force:
        record = json.loads(destination.read_text(encoding='utf-8'))
        if record.get('settings') != current:
            raise ValueError('CPU transcript settings mismatch')
        result = record.get('transcript')
        validate_transcript(result, len(pcm)/32000)
        if record.get('transcript_sha256') != transcript_sha(result):
            raise ValueError('CPU transcript checksum mismatch')
        return result, dict(transcript_cache_hit=True, cache_key=key, settings=current,
                            transcription_identity=current,
                            transcript_cache_read_seconds=time.perf_counter()-started)
    model_path, timing = model_directory(cache, protected)
    transcribe_started = time.perf_counter()
    result = transcribe(pcm, model_path)
    validate_transcript(result, len(pcm)/32000)
    save(destination, dict(settings=current, transcript=result, transcript_sha256=transcript_sha(result)), protected)
    return result, dict(transcript_cache_hit=False, cache_key=key, settings=current,
                        transcription_identity=current, **timing,
                        transcribe_seconds=time.perf_counter()-transcribe_started,
                        cache_miss_total_seconds=time.perf_counter()-started)
