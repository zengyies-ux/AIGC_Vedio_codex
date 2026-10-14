#!/usr/bin/env python3
"""Local English audio estimates; script text remains authoritative."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import wave
import xml.etree.ElementTree as ET
import zipfile

MODEL = "mlx-community/whisper-small.en-mlx"
REVISION = "52a88bf6e98b114a210c21bb83e22d6e1505cb73"
PARAMS = dict(language="en", task="transcribe", word_timestamps=True,
              temperature=0.0, condition_on_previous_text=True, verbose=None)
VERSION = "2"
MATCHING_NORMALIZATION = "limited_spelling_v1"
# User-confirmed spelling equivalence only; no fuzzy edits, names or numbers.
SPELLING_EQUIVALENTS = {"cancelled": "canceled"}
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tokens(text: str) -> list[str]:
    return [SPELLING_EQUIVALENTS.get(word, word) for word in raw_tokens(text)]


def raw_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?|\d+(?:\.\d+)?", text.lower().replace("’", "'"))


def ensure_no_collisions(outputs: list[Path], inputs: list[Path]) -> None:
    for output in outputs:
        for source in inputs:
            same = output.resolve() == source.resolve()
            if not same and output.exists() and source.exists():
                same = output.samefile(source)
            if same:
                raise ValueError(f"Input/output collision: {source}; choose another output/cache directory")


def save(path: Path, value, protected: list[Path] = ()) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    ensure_no_collisions([path, temporary], protected)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def transcript_sha(transcript: dict) -> str:
    return digest(json.dumps(transcript, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode())


def validate_transcript(transcript: dict, duration: float) -> None:
    if not isinstance(transcript, dict) or not isinstance(transcript.get("text"), str) or not isinstance(transcript.get("segments"), list):
        raise ValueError("Invalid transcript schema; explicitly --force-transcribe to regenerate")
    last_start = last_end = 0.0
    for segment in transcript["segments"]:
        if not isinstance(segment, dict) or not isinstance(segment.get("words"), list):
            raise ValueError("Cached segment requires words; explicitly --force-transcribe")
        for word in segment["words"]:
            if not isinstance(word, dict) or not isinstance(word.get("word"), str):
                raise ValueError("Invalid cached word schema; explicitly --force-transcribe")
            start, end = word.get("start"), word.get("end")
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in [start, end]):
                raise ValueError("Nonfinite cached word timestamp; explicitly --force-transcribe")
            if start < 0 or end < start or start < last_start or end < last_end or end > duration + .05:
                raise ValueError("Nonmonotone/out-of-range cached timestamp; explicitly --force-transcribe")
            probability = word.get("probability")
            if probability is not None and (isinstance(probability, bool) or not isinstance(probability, (int, float)) or not math.isfinite(probability) or not 0 <= probability <= 1):
                raise ValueError("Invalid cached probability; explicitly --force-transcribe")
            last_start, last_end = start, end


def read_script(path: Path, episode: int | None) -> list[dict]:
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text())
        units = value["units"] if isinstance(value, dict) else value
        if not units or any(not u.get("text") or not u.get("id") for u in units):
            raise ValueError("script JSON requires nonempty units with id and text")
        if len({u["id"] for u in units}) != len(units):
            raise ValueError("script unit ids must be unique")
        return units
    active = episode is None
    units = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        match = re.match(r"\[P(\d+)\]\s*(.*)", line)
        unit_id, text = ("P" + match[1], match[2]) if match else (f"L{line_number}", line.strip())
        header = re.fullmatch(r"(?:Episode|EP)\s*(\d+)", text, re.I)
        if header:
            if active and episode is not None:
                break
            active = episode is None or int(header[1]) == episode
            continue
        if active and text:
            kind = "dialogue" if text.startswith(('"', '“', '「')) else "narration"
            units.append(dict(id=unit_id, text=text, kind=kind, speaker=None))
    if not units:
        raise ValueError("No script units found; check episode and input")
    return units


def green_groups(path: Path) -> list[list[str]]:
    """Read run-level green labels without rendering or inventing comments."""
    with zipfile.ZipFile(path) as z:
        body = ET.fromstring(z.read("word/document.xml"))
    groups, current = [], []
    for paragraph in body.findall(".//w:body/w:p", NS):
        text = "".join(n.text or "" for n in paragraph.findall(".//w:t", NS))
        marked = False
        for run in paragraph.findall("w:r", NS):
            highlight = run.find("w:rPr/w:highlight", NS)
            shading = run.find("w:rPr/w:shd", NS)
            marked |= highlight is not None and highlight.get("{" + NS["w"] + "}val") == "green"
            marked |= shading is not None and shading.get("{" + NS["w"] + "}fill", "").lower() in {"00ff00", "92d050"}
        clean = re.split(r"——\s*区间", text, maxsplit=1)[0].strip()
        # Chinese notes are not interchangeable with the English audio script.
        if marked and re.search(r"[A-Za-z]", clean):
            current.append(clean)
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def align(expected: list[str], heard: list[str]) -> tuple[dict[int, int], list[int]]:
    """Monotone global edit alignment prevents greedy reuse of repeated lines.

    Only exact normalized tokens supply time boundaries. Substitutions and
    deletions stay visible as missing tokens, rather than silently timing them.
    """
    n, m = len(expected), len(heard)
    directions = [bytearray(m + 1) for _ in range(n + 1)]
    previous = list(range(m + 1))
    for j in range(1, m + 1):
        directions[0][j] = 2
    for i in range(1, n + 1):
        row = [i] + [0] * m
        directions[i][0] = 1
        for j in range(1, m + 1):
            diagonal = previous[j - 1] + (0 if expected[i - 1] == heard[j - 1] else 2)
            deletion, insertion = previous[j] + 1, row[j - 1] + 1
            cost = min(diagonal, deletion, insertion)
            row[j] = cost
            directions[i][j] = 0 if diagonal == cost else (1 if deletion == cost else 2)
        previous = row
    mapping, unused, i, j = {}, [], n, m
    while i or j:
        step = directions[i][j]
        if step == 0:
            if expected[i - 1] == heard[j - 1]:
                mapping[i - 1] = j - 1
            else:
                unused.append(j - 1)
            i, j = i - 1, j - 1
        elif step == 1:
            i -= 1
        else:
            unused.append(j - 1)
            j -= 1
    return mapping, sorted(unused)


def match_units(units: list[dict], transcript: dict) -> dict:
    heard, heard_original, word_times = [], [], []
    for segment in transcript["segments"]:
        for word in segment.get("words", []):
            for token in raw_tokens(word["word"]):
                heard_original.append(token)
                heard.append(SPELLING_EQUIVALENTS.get(token, token))
                word_times.append(word)
    expected, expected_original, spans = [], [], []
    for unit in units:
        words = tokens(unit["text"])
        expected_original.extend(raw_tokens(unit["text"]))
        spans.append((len(expected), len(expected) + len(words)))
        expected.extend(words)
    mapping, unused = align(expected, heard)
    rows = []
    for unit, (begin, end) in zip(units, spans):
        found = [i for i in range(begin, end) if i in mapping]
        missing = [expected[i] for i in range(begin, end) if i not in mapping]
        start = word_times[mapping[found[0]]]["start"] if found else None
        finish = word_times[mapping[found[-1]]]["end"] if found else None
        boundary_complete = bool(found) and begin in mapping and end - 1 in mapping
        issues = []
        if missing:
            issues.append("missing_or_asr_changed_tokens")
        if not boundary_complete:
            issues.append("incomplete_boundary")
        if start is not None and finish <= start:
            issues.append("zero_or_negative_estimated_duration")
        if end - begin <= 2:
            issues.append("short_phrase_requires_context_review")
        if found and any(word_times[mapping[i]].get("probability", 1) < 0.5 for i in found):
            issues.append("low_word_probability")
        equivalences = [dict(script_token=expected_original[i], asr_token=heard_original[mapping[i]],
            canonical_token=expected[i], script_token_index=i - begin, asr_token_index=mapping[i],
            source="user_confirmed_cancelled_canceled_spelling") for i in found
            if expected_original[i] != heard_original[mapping[i]]]
        rows.append({**unit, "estimated_start": start, "estimated_end": finish,
                     "exact_tokens": len(found), "script_tokens": end - begin,
                     "spelling_equivalences": equivalences,
                     "missing_tokens": missing, "issues": issues,
                     "boundary_status": "not_playback_verified"})
    repeated = {}
    for row in rows:
        repeated.setdefault(tuple(tokens(row["text"])), []).append(row)
    for candidates in repeated.values():
        if len(candidates) > 1 and any(r["missing_tokens"] for r in candidates):
            # A global alignment tie cannot prove which identical occurrence
            # was removed. Flag every affected occurrence, including the one
            # receiving a numerical estimate.
            for row in candidates:
                row["issues"].append("ambiguous_repeat")
                row["boundary_status"] = "ambiguous_repeat_not_playback_verified"
    return dict(units=rows, exact_tokens=len(mapping), script_tokens=len(expected),
                matching_normalization=MATCHING_NORMALIZATION,
                equivalent_tokens=sum(len(r["spelling_equivalences"]) for r in rows),
                asr_tokens=len(heard), unused_asr_tokens=[dict(token=heard[i],
                start=word_times[i]["start"], end=word_times[i]["end"]) for i in unused])


def decode(audio: Path) -> tuple[bytes, str]:
    import imageio_ffmpeg
    executable = imageio_ffmpeg.get_ffmpeg_exe()
    pcm = subprocess.run([executable, "-nostdin", "-loglevel", "error", "-i", str(audio),
                          "-threads", "0", "-f", "s16le", "-ac", "1", "-acodec", "pcm_s16le",
                          "-ar", "16000", "-"], capture_output=True, check=True).stdout
    if not pcm or len(pcm) % 2:
        raise ValueError("Empty or malformed decoded PCM")
    version = subprocess.run([executable, "-version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    return pcm, version


def configured_versions() -> dict:
    names = ["mlx", "mlx-whisper", "imageio-ffmpeg", "numpy", "numba", "scipy", "tiktoken", "torch", "huggingface-hub"]
    return {name: importlib.metadata.version(name) for name in names}


def model_directory(cache: Path, protected: list[Path] = ()) -> tuple[str, dict]:
    """Verify a pinned local model without any network call on warm runs."""
    model = cache / "model"
    manifest = model / "local_manifest.json"
    ensure_no_collisions([manifest, manifest.with_suffix(".json.tmp"), model / "config.json", model / "weights.npz"], protected)
    started = time.perf_counter()
    if manifest.exists():
        record = json.loads(manifest.read_text())
        if record.get("model") != MODEL or record.get("revision") != REVISION:
            raise ValueError("Local model repo/revision mismatch; use a separate cache")
        for name in ("config.json", "weights.npz"):
            if not (model / name).is_file() or digest((model / name).read_bytes()) != record["files"].get(name):
                raise ValueError(f"Local model integrity failed: {name}; do not silently reuse")
        return str(model), dict(model_local_verified=True,
            model_integrity_check_seconds=time.perf_counter() - started, model_download_seconds=0)
    from huggingface_hub import snapshot_download
    download_started = time.perf_counter()
    path = snapshot_download(MODEL, revision=REVISION,
        allow_patterns=["config.json", "weights.npz"], local_dir=model)
    download_seconds = time.perf_counter() - download_started
    record = dict(model=MODEL, revision=REVISION,
        files={name: digest((model / name).read_bytes()) for name in ("config.json", "weights.npz")})
    save(manifest, record, protected)
    return str(path), dict(model_local_verified=True, model_download_seconds=download_seconds,
        model_first_download_and_integrity_seconds=time.perf_counter() - started)


def get_transcript(pcm: bytes, cache: Path, force: bool = False, protected: list[Path] = ()) -> tuple[dict, dict]:
    settings = dict(format_version=VERSION, pcm_sha256=digest(pcm),
                    pcm_format="16000 Hz mono s16le", model=MODEL, revision=REVISION,
                    parameters=PARAMS, tool_versions=configured_versions())
    key = digest(json.dumps(settings, sort_keys=True).encode())
    destination = cache / "transcripts" / (key + ".json")
    ensure_no_collisions([destination, destination.with_suffix(".json.tmp")], protected)
    started = time.perf_counter()
    if destination.exists() and not force:
        try:
            stored = json.loads(destination.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("Unreadable cached transcript; explicitly --force-transcribe to regenerate") from error
        if not isinstance(stored, dict):
            raise ValueError("Invalid cache schema; explicitly --force-transcribe to regenerate")
        if stored.get("settings") != settings:
            raise ValueError("Cached transcription settings mismatch")
        validate_transcript(stored.get("transcript"), len(pcm) / 32000)
        if stored.get("transcript_sha256") != transcript_sha(stored.get("transcript")):
            raise ValueError("Cached transcript checksum mismatch; explicitly --force-transcribe to regenerate")
        return stored["transcript"], dict(transcript_cache_hit=True,
            transcript_cache_read_seconds=time.perf_counter() - started, cache_key=key, settings=settings)
    os.environ["HF_HOME"] = str(cache / "hf-cache")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["NUMBA_CACHE_DIR"] = str(cache / "numba-cache")
    model_path, model_timing = model_directory(cache, protected)
    import_started = time.perf_counter()
    import numpy as np
    import mlx_whisper
    import mlx.core as mx
    import_seconds = time.perf_counter() - import_started
    signal = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    transcribe_started = time.perf_counter()
    transcript = mlx_whisper.transcribe(signal, path_or_hf_repo=str(model_path), **PARAMS)
    mx.synchronize()
    transcribe_seconds = time.perf_counter() - transcribe_started
    validate_transcript(transcript, len(pcm) / 32000)
    save(destination, dict(settings=settings, transcript=transcript,
        transcript_sha256=transcript_sha(transcript)), protected)
    return transcript, dict(transcript_cache_hit=False, cache_key=key, settings=settings,
        **model_timing, backend_import_seconds=import_seconds, transcribe_seconds=transcribe_seconds,
        cache_miss_total_seconds=time.perf_counter() - started)


def add_groups(rows: list[dict], groups: list[list[str]]) -> tuple[list[dict], list[str]]:
    output, warnings = [], []
    by_text = {}
    for row in rows:
        by_text.setdefault(tuple(tokens(row["text"])), []).append(row)
    used = set()
    for number, group in enumerate(groups, 1):
        matched = []
        for text in group:
            candidates = [r for r in by_text.get(tuple(tokens(text)), []) if r["id"] not in used]
            if len(candidates) != 1:
                warnings.append(f"group_{number}: source text missing or ambiguous in script")
                continue
            matched.append(candidates[0]); used.add(candidates[0]["id"])
        starts = [r["estimated_start"] for r in matched if r["estimated_start"] is not None]
        ends = [r["estimated_end"] for r in matched if r["estimated_end"] is not None]
        output.append(dict(id=f"dialogue_{number:02}", unit_ids=[r["id"] for r in matched],
            script_text=group, source_count=len(group), matched_count=len(matched),
            estimated_start=min(starts) if starts else None, estimated_end=max(ends) if ends else None,
            issues=sorted({x for r in matched for x in r["issues"]}),
            boundary_status="not_playback_verified"))
    ungrouped = [r["id"] for r in rows if r.get("kind") == "dialogue" and r["id"] not in used]
    if ungrouped:
        warnings.append("script_dialogue_not_in_green_groups: " + ", ".join(ungrouped))
    return output, warnings


def script_dialogue_groups(rows: list[dict]) -> list[dict]:
    """Use GPT-supplied units/roles, with optional explicit group labels.

    Unit ids preserve identical complete replies. Quotes never infer a role.
    Without a label, consecutive dialogue is one group, split by narration.
    """
    batches, current, previous_label = [], [], None
    for row in rows:
        label = row.get("dialogue_group")
        if row.get("kind") != "dialogue":
            if current:
                batches.append(current)
            current, previous_label = [], None
            continue
        if current and label != previous_label:
            batches.append(current)
            current = []
        current.append(row)
        previous_label = label
    if current:
        batches.append(current)
    output = []
    for number, batch in enumerate(batches, 1):
        starts = [r["estimated_start"] for r in batch if r["estimated_start"] is not None]
        ends = [r["estimated_end"] for r in batch if r["estimated_end"] is not None]
        output.append(dict(id=f"dialogue_{number:02}", unit_ids=[r["id"] for r in batch],
            script_text=[r["text"] for r in batch], source_count=len(batch), matched_count=len(batch),
            estimated_start=min(starts) if starts else None, estimated_end=max(ends) if ends else None,
            issues=sorted({issue for r in batch for issue in r["issues"]}),
            boundary_status="not_playback_verified"))
    return output


def read_reference(path: Path) -> dict:
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate reference key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique_keys)


def valid_number(value) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


def alignment_blockers(dialogues: list[dict], anchors: list[dict], matched: dict,
                       requested_anchor_ids: list[str] = ()) -> list[str]:
    """Shared content checks; neither a reference nor a reply can hide missing text."""
    blockers = []
    if set(requested_anchor_ids) != {p["id"] for p in anchors}:
        blockers.append("requested_anchor_not_matched")
    if matched.get("script_tokens", 0) <= 0 or matched.get("exact_tokens") != matched.get("script_tokens"):
        blockers.append("script_alignment_incomplete")
    hard_issues = {"missing_or_asr_changed_tokens", "incomplete_boundary", "ambiguous_repeat",
                   "zero_or_negative_estimated_duration"}
    rows = matched.get("units", [])
    for row in rows:
        for issue in hard_issues.intersection(row.get("issues", [])):
            blockers.append(f"{row['id']}:{issue}")
        if row.get("kind") == "dialogue" and not known_role(row.get("speaker")):
            blockers.append(f"{row['id']}:script_speaker_not_provided")
    if any(r.get("kind") == "dialogue" for r in rows) and not dialogues:
        blockers.append("dialogue_groups_not_provided")
    grouped_ids = []
    for group in dialogues:
        if not group.get("source_count") or group.get("source_count") != group.get("matched_count") or len(group.get("unit_ids", [])) != group.get("source_count"):
            blockers.append(f"{group['id']}:source_group_pairing_incomplete")
        grouped_ids.extend(group.get("unit_ids", []))
    if len(set(grouped_ids)) != len(grouped_ids):
        blockers.append("dialogue_unit_reused_across_groups")
    if set(grouped_ids) != {r["id"] for r in rows if r.get("kind") == "dialogue"}:
        blockers.append("script_dialogue_group_coverage_incomplete")
    starts = [r.get("estimated_start") for r in rows]
    ends = [r.get("estimated_end") for r in rows]
    if not rows or not all(valid_number(v) for v in starts + ends):
        blockers.append("script_unit_timing_incomplete")
    else:
        body_start, body_end = min(starts), max(ends)
        for word in matched.get("unused_asr_tokens", []):
            begin, end = word.get("start"), word.get("end")
            if not valid_number(begin) or not valid_number(end) or end < begin:
                blockers.append("unmatched_asr_timing_invalid")
            elif (begin < body_end and end > body_start) or (begin == end and body_start < begin < body_end):
                blockers.append("unmatched_asr_inside_script_body")
                break
    return list(dict.fromkeys(blockers))


def evaluate_reference(dialogues: list[dict], anchors: list[dict], matched: dict,
                       reference: dict | None, audio_sha: str,
                       requested_anchor_ids: list[str] = ()) -> dict:
    """Adoption by explicit user references; never claim playback accuracy."""
    outcome = dict(automatic_pass=False, adoption_status="no_user_reference",
                   tolerance_seconds=2.0, comparison_points=[], blockers=[],
                   maximum_absolute_difference_seconds=None,
                   playback_verified=False, measured_boundary_error_seconds=None)
    if reference is None:
        outcome["blockers"] = ["user_reference_not_provided"]
        return outcome
    blockers = outcome["blockers"]
    outcome["adoption_status"] = "user_reference_not_passed"
    if not isinstance(reference, dict):
        blockers.append("reference_schema_invalid")
        return outcome
    if reference.get("basis") != "user_supplied":
        blockers.append("reference_basis_not_user_supplied")
    if reference.get("audio_file_sha256") != audio_sha:
        blockers.append("reference_audio_fingerprint_mismatch")
    tolerance = reference.get("tolerance_seconds")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance != 2.0:
        blockers.append("reference_tolerance_must_be_2_seconds")
    refs_d, refs_a = reference.get("dialogue_groups"), reference.get("anchors")
    if not isinstance(refs_d, dict) or not isinstance(refs_a, dict):
        blockers.append("reference_groups_or_anchors_missing")
        return outcome
    ids_d = {p["id"] for p in dialogues}
    ids_a = set(requested_anchor_ids or [p["id"] for p in anchors])
    if set(refs_d) != ids_d:
        blockers.append("reference_dialogue_point_set_mismatch")
    if set(refs_a) != ids_a or {p["id"] for p in anchors} != ids_a:
        blockers.append("reference_anchor_point_set_mismatch")
    blockers.extend(alignment_blockers(dialogues, anchors, matched, list(ids_a)))
    for category, points, refs in [("dialogue", dialogues, refs_d), ("anchor", anchors, refs_a)]:
        for point in points:
            item = refs.get(point["id"])
            fields = ["start", "end"] if category == "dialogue" else ["start"]
            if not isinstance(item, dict) or not all(valid_number(item.get(field)) for field in fields):
                blockers.append(f"{point['id']}:reference_boundary_missing_or_invalid")
                continue
            if category == "dialogue" and item["end"] <= item["start"]:
                blockers.append(f"{point['id']}:reference_interval_invalid")
                continue
            if not all(valid_number(point.get("estimated_" + field)) for field in fields):
                blockers.append(f"{point['id']}:estimated_boundary_missing_or_invalid")
                continue
            differences = {field + "_difference_seconds": point["estimated_" + field] - item[field] for field in fields}
            maximum = max(abs(v) for v in differences.values())
            passed = maximum <= 2.0 + 1e-9
            outcome["comparison_points"].append(dict(id=point["id"], **differences,
                maximum_absolute_difference_seconds=maximum, passed=passed))
            if not passed:
                blockers.append(f"{point['id']}:reference_difference_exceeds_2_seconds")
    if outcome["comparison_points"]:
        outcome["maximum_absolute_difference_seconds"] = max(p["maximum_absolute_difference_seconds"] for p in outcome["comparison_points"])
    else:
        blockers.append("no_reference_points_compared")
    outcome["blockers"] = list(dict.fromkeys(blockers))
    outcome["automatic_pass"] = not outcome["blockers"]
    if outcome["automatic_pass"]:
        outcome["adoption_status"] = "user_reference_passed"
    return outcome


def make_candidate(audio_sha: str, pcm_sha: str, duration: float, matched: dict,
                   dialogues: list[dict], anchors: list[dict], requested_anchors: list[dict],
                   warnings: list[str], source_content_hashes: dict) -> dict:
    """Stable complete candidate identity, without paths, runtime or reply data."""
    value = dict(candidate_schema="2", audio_file_sha256=audio_sha, decoded_pcm_sha256=pcm_sha,
                decoded_duration_seconds=duration, source_origin_seconds=0,
                source_content_hashes=source_content_hashes, matching=matched,
                dialogue_groups=dialogues, anchors=anchors, requested_anchors=requested_anchors,
                warnings=warnings)
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def audio_content_identity(candidate: dict) -> str:
    """Audio, authoritative text/roles and matched evidence; excludes derived cuts."""
    fields = ["audio_file_sha256", "decoded_pcm_sha256", "decoded_duration_seconds",
              "source_origin_seconds", "matching", "dialogue_groups"]
    value = {key: candidate[key] for key in fields}
    value["identity_schema"] = "2"
    value["source_content_hashes"] = {key: sha for key, sha in candidate["source_content_hashes"].items()
                                      if key != "anchors"}
    return transcript_sha(value)


def derived_anchors_identity(candidate: dict) -> str:
    return transcript_sha(dict(anchors=candidate["anchors"], requested_anchors=candidate["requested_anchors"]))


def known_role(value) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {
        "unknown", "unspecified", "tbd", "none", "null", "?", "unknown speaker", "unknown listener",
        "未知", "未确认", "待确认", "待定", "不明", "未提供", "未核定", "未确定"}


def candidate_blockers(candidate: dict) -> list[str]:
    blockers = alignment_blockers(candidate["dialogue_groups"], candidate["anchors"],
        candidate["matching"], [p["id"] for p in candidate["requested_anchors"]])
    rows = candidate["matching"]["units"]
    by_id = {row["id"]: row for row in rows}
    duration = candidate["decoded_duration_seconds"]
    for row in rows:
        if row.get("kind") not in ("narration", "dialogue"):
            blockers.append(f"{row['id']}:script_kind_not_provided")
        if row.get("kind") == "dialogue":
            if not known_role(row.get("speaker")):
                blockers.append(f"{row['id']}:script_speaker_not_provided")
            listeners = row.get("listeners", row.get("listener"))
            if not (known_role(listeners) or isinstance(listeners, list) and listeners and all(known_role(v) for v in listeners)):
                blockers.append(f"{row['id']}:script_listener_not_provided")
        begin, end = row.get("estimated_start"), row.get("estimated_end")
        if not valid_number(begin) or not valid_number(end) or end <= begin or end > duration:
            blockers.append(f"{row['id']}:candidate_boundary_invalid")
    if not rows:
        blockers.append("no_sentence_candidates")
    for anchor in candidate["anchors"]:
        row = by_id.get(anchor.get("unit_id"))
        if row is None or any(anchor.get(field) != row.get(field) for field in ("estimated_start", "estimated_end")):
            blockers.append(f"{anchor['id']}:derived_anchor_mapping_invalid")
    return list(dict.fromkeys(blockers))


def evaluate_confirmation(candidate: dict, confirmation: dict | None) -> dict:
    """Record explicit consent to these candidates, never invent a timing reference."""
    candidate_sha = transcript_sha(candidate)
    blockers = candidate_blockers(candidate)
    outcome = dict(automatic_pass=False, adoption_status="candidate_pending_user_confirmation",
        candidate_content_sha256=candidate_sha, blockers=blockers, confirmation_fact=None,
        audio_content_identity_sha256=audio_content_identity(candidate),
        derived_anchors_sha256=derived_anchors_identity(candidate),
        adoption_source=None, scheme_approval=dict(approved=False, source=None),
        user_confirmation_recorded=False, simulated_adoption_pass=False,
        playback_verified=False, measured_boundary_error_seconds=None,
        maximum_absolute_difference_seconds=None, comparison_points=[])
    if confirmation is None:
        if blockers:
            outcome["adoption_status"] = "candidate_requires_correction"
        return outcome
    outcome["adoption_status"] = "candidate_confirmation_not_passed"
    if not isinstance(confirmation, dict):
        blockers.append("confirmation_schema_invalid")
        return outcome
    if confirmation.get("audio_file_sha256") != candidate["audio_file_sha256"]:
        blockers.append("confirmation_audio_fingerprint_mismatch")
    if "audio_content_identity_sha256" in confirmation:
        if confirmation.get("audio_content_identity_sha256") != audio_content_identity(candidate):
            blockers.append("confirmation_audio_content_identity_mismatch")
    elif confirmation.get("candidate_content_sha256") != candidate_sha:
        # Old full-candidate records remain strict, including their old anchors.
        blockers.append("confirmation_candidate_fingerprint_mismatch")
    if confirmation.get("confirmed") is not True:
        blockers.append("explicit_candidate_confirmation_required")
    basis = confirmation.get("basis")
    if basis not in ("user_explicit", "test_simulation"):
        blockers.append("confirmation_basis_invalid")
    note = confirmation.get("confirmation_note")
    if basis == "user_explicit" and (not isinstance(note, str) or not note.strip()):
        blockers.append("confirmation_reply_missing")
    # Store a fact only for an exact affirmative tied to the current content.
    consent_errors = [b for b in blockers if b.startswith("confirmation_") or b == "explicit_candidate_confirmation_required"]
    if not consent_errors:
        outcome["confirmation_fact"] = {**confirmation,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
        outcome["user_confirmation_recorded"] = basis == "user_explicit"
    outcome["blockers"] = list(dict.fromkeys(blockers))
    if not blockers:
        if basis == "test_simulation":
            outcome["simulated_adoption_pass"] = True
            outcome["adoption_status"] = "candidate_confirmation_simulated"
        else:
            outcome["automatic_pass"] = True
            outcome["adoption_status"] = "user_confirmed_candidates"
            outcome["adoption_source"] = "user_overall_confirmation"
            current_scheme = (confirmation.get("derived_anchors_sha256") == derived_anchors_identity(candidate)
                              if "audio_content_identity_sha256" in confirmation else True)
            outcome["scheme_approval"] = dict(approved=current_scheme, source="user_overall_confirmation",
                scope="original_overall_reply", covers_current_derived_anchors=current_scheme,
                confirmed_derived_anchors_sha256=confirmation.get("derived_anchors_sha256"),
                confirmation_note=note)
    return outcome


def evaluate_internal_review(candidate: dict, review: dict | None) -> dict:
    """Accept a recorded content/role/boundary check, never merely a bypass flag."""
    blockers = candidate_blockers(candidate)
    outcome = dict(checked=False, blockers=blockers, review_fact=None, simulated=False,
        audio_content_identity_sha256=audio_content_identity(candidate),
        derived_anchors_sha256=derived_anchors_identity(candidate))
    if not isinstance(review, dict):
        blockers.append("gpt_internal_review_required")
        return outcome
    if review.get("basis") not in ("gpt_internal_review", "test_simulation"):
        blockers.append("internal_review_basis_invalid")
    if review.get("checked") is not True:
        blockers.append("internal_review_not_completed")
    for field, expected in [("audio_file_sha256", candidate["audio_file_sha256"]),
            ("audio_content_identity_sha256", audio_content_identity(candidate)),
            ("derived_anchors_sha256", derived_anchors_identity(candidate))]:
        if review.get(field) != expected:
            blockers.append("internal_review_" + field + "_mismatch")
    for field in ("project_scope", "review_source", "review_note"):
        if not isinstance(review.get(field), str) or not review[field].strip():
            blockers.append("internal_review_" + field + "_missing")
    checks = review.get("checks")
    if not isinstance(checks, dict) or any(checks.get(field) is not True for field in
            ("content_complete", "roles_verified", "boundaries_verified")):
        blockers.append("internal_review_checks_incomplete")
    if review.get("reviewed_unit_ids") != [row["id"] for row in candidate["matching"]["units"]]:
        blockers.append("internal_review_unit_coverage_incomplete")
    if review.get("unresolved_blockers") != []:
        blockers.append("internal_review_unresolved_blockers")
    outcome["blockers"] = list(dict.fromkeys(blockers))
    if not blockers:
        outcome["checked"] = True
        outcome["simulated"] = review["basis"] == "test_simulation"
        outcome["review_fact"] = {**review, "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
    return outcome


def evaluate_adoption(candidate: dict, confirmation: dict | None = None,
                      internal_review: dict | None = None, mode_record: dict | None = None) -> dict:
    """Default one-review verification; routine requires persisted user authority.

    Both paths consume current alignment and a bound internal review. A new
    derived anchor needs a new internal check, not another unchanged-audio reply.
    """
    outcome = evaluate_confirmation(candidate, confirmation)
    review = evaluate_internal_review(candidate, internal_review)
    outcome["internal_review"] = review
    mode = mode_record.get("mode") if isinstance(mode_record, dict) else "verification"
    outcome["production_mode"] = mode
    if mode not in ("verification", "routine") or mode_record is not None and not isinstance(mode_record, dict):
        outcome["blockers"].append("production_mode_invalid")
        outcome["automatic_pass"] = False
        outcome["adoption_status"] = "production_mode_not_passed"
        return outcome
    if mode == "verification":
        outcome["blockers"] = list(dict.fromkeys(outcome["blockers"] + review["blockers"]))
        if not review["checked"]:
            outcome["automatic_pass"] = False
            outcome["simulated_adoption_pass"] = False
            outcome["adoption_source"] = None
            if not candidate_blockers(candidate):
                outcome["adoption_status"] = "candidate_pending_internal_review"
        elif review["simulated"]:
            outcome["simulated_adoption_pass"] = outcome["automatic_pass"] or outcome["simulated_adoption_pass"]
            outcome["automatic_pass"] = False
            outcome["adoption_source"] = None
            outcome["scheme_approval"] = dict(approved=False, source=None)
            outcome["user_confirmation_recorded"] = False
            outcome["confirmation_fact"] = None
            outcome["adoption_status"] = "candidate_confirmation_simulated"
        return outcome
    blockers = list(review["blockers"])
    if mode_record.get("basis") not in ("user_explicit", "test_simulation"):
        blockers.append("routine_authorization_basis_invalid")
    if mode_record.get("authorized") is not True:
        blockers.append("routine_authorization_required")
    for field in ("project_scope", "authorization_source", "authorization_note"):
        if not isinstance(mode_record.get(field), str) or not mode_record[field].strip():
            blockers.append("routine_" + field + "_missing")
    if isinstance(internal_review, dict) and mode_record.get("project_scope") != internal_review.get("project_scope"):
        blockers.append("routine_authorization_scope_mismatch")
    # Routine does not turn an optional audio reply into scheme approval.
    outcome.update(automatic_pass=False, simulated_adoption_pass=False,
        user_confirmation_recorded=False, confirmation_fact=None, adoption_source=None,
        scheme_approval=dict(approved=False, source=None), blockers=list(dict.fromkeys(blockers)),
        adoption_status="internal_adoption_not_passed", routine_authorization_fact=None)
    if not blockers:
        simulated = mode_record["basis"] == "test_simulation" or review["simulated"] or (
            isinstance(confirmation, dict) and confirmation.get("basis") == "test_simulation")
        if simulated:
            outcome["simulated_adoption_pass"] = True
            outcome["adoption_status"] = "internal_adoption_simulated"
        else:
            outcome["automatic_pass"] = True
            outcome["adoption_status"] = "internally_adopted_candidates"
            outcome["adoption_source"] = "gpt_internal_review"
            outcome["routine_authorization_fact"] = mode_record
    return outcome


def write_clips(pcm: bytes, points: list[dict], output: Path) -> list[dict]:
    duration, clips = len(pcm) / 32000, []
    folder = output / "review_clips"
    folder.mkdir(parents=True, exist_ok=True)
    for point in points:
        if point.get("estimated_start") is None or point.get("estimated_end") is None:
            continue
        begin = max(0.0, point["estimated_start"] - 0.7)
        end = min(duration, point["estimated_end"] + 0.7)
        if end <= begin:
            continue
        clip = folder / (re.sub(r"[^a-zA-Z0-9_-]", "_", point["id"]) + ".wav")
        with wave.open(str(clip), "wb") as writer:
            writer.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            writer.writeframes(pcm[round(begin * 16000) * 2:round(end * 16000) * 2])
        clips.append(dict(id=point["id"], path=str(clip.absolute()),
            source_offset_seconds=round(begin, 4), source_end_seconds=round(end, 4),
            local_estimated_start=round(point["estimated_start"] - begin, 4),
            local_estimated_end=round(point["estimated_end"] - begin, 4)))
    return clips


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--episode", type=int)
    parser.add_argument("--dialogue-docx", type=Path)
    parser.add_argument("--anchors-json", type=Path, help="list of {id, unit_id}; historical_seconds is comparison only")
    parser.add_argument("--reference-times-json", type=Path, help="explicit user reference boundaries and audio SHA; adoption tolerance 2 seconds")
    parser.add_argument("--candidate-confirmation-json", type=Path, help="explicit reply tied to the audio and complete candidate hashes; not a timing reference")
    parser.add_argument("--internal-review-json", type=Path, help="GPT content/role/boundary check bound to audio identity and current derived anchors")
    parser.add_argument("--production-mode-json", type=Path, help="persisted verification mode, or user-authorized routine mode; absent means verification")
    parser.add_argument("--cache", type=Path, default=Path(".codex_tmp/audio_v3"))
    parser.add_argument("--out", type=Path, default=Path(".codex_tmp/audio_v3/result"))
    parser.add_argument("--force-transcribe", action="store_true", help="performance benchmark only; bypass transcript cache")
    args = parser.parse_args()
    if args.reference_times_json and (args.candidate_confirmation_json or args.internal_review_json or args.production_mode_json):
        raise ValueError("Choose legacy user reference comparison or candidate adoption, not both")
    started = time.perf_counter()
    cache, output = args.cache.absolute(), args.out.absolute()
    inputs = [p for p in [args.audio, args.script, args.dialogue_docx, args.anchors_json,
                          args.reference_times_json, args.candidate_confirmation_json,
                          args.internal_review_json, args.production_mode_json] if p is not None]
    request_path = output / "candidate_confirmation_request.json"
    internal_request = output / "internal_review_request.json"
    planned = [output / "result.json", output / "result.json.tmp", output / "review.md",
               request_path, request_path.with_suffix(".json.tmp"), internal_request,
               internal_request.with_suffix(".json.tmp")]
    ensure_no_collisions(planned, inputs)
    source_hashes = {str(p.absolute()): digest(p.read_bytes()) for p in inputs}
    reference = read_reference(args.reference_times_json) if args.reference_times_json else None
    confirmation = read_reference(args.candidate_confirmation_json) if args.candidate_confirmation_json else None
    internal_review = read_reference(args.internal_review_json) if args.internal_review_json else None
    mode_record = read_reference(args.production_mode_json) if args.production_mode_json else None
    units = read_script(args.script, args.episode)
    if args.dialogue_docx:
        groups = green_groups(args.dialogue_docx)
    else:
        previews = [{**u, "estimated_start": None, "estimated_end": None, "issues": []} for u in units]
        groups = script_dialogue_groups(previews)
    requested_anchors = json.loads(args.anchors_json.read_text()) if args.anchors_json else []
    point_ids = [f"dialogue_{n:02}" for n in range(1, len(groups) + 1)] + [p["id"] for p in requested_anchors]
    if any(not isinstance(label, str) or not label for label in point_ids):
        raise ValueError("Review point ids must be nonempty strings")
    clip_names = [re.sub(r"[^a-zA-Z0-9_-]", "_", label) + ".wav" for label in point_ids]
    if len(set(point_ids)) != len(point_ids) or len({name.casefold() for name in clip_names}) != len(clip_names):
        raise ValueError("Duplicate/sanitized review clip names; choose unique ids to preserve time mapping")
    clip_outputs = [output / "review_clips" / name for name in clip_names]
    ensure_no_collisions(clip_outputs, inputs)
    decode_started = time.perf_counter()
    pcm, decoder_version = decode(args.audio)
    decode_seconds = time.perf_counter() - decode_started
    transcript, timing = get_transcript(pcm, cache, args.force_transcribe, inputs)
    transcript_path = cache / "transcripts" / (timing["cache_key"] + ".json") if timing.get("cache_key") else None
    protected_results = inputs + ([transcript_path] if transcript_path else [])
    ensure_no_collisions(planned + clip_outputs, protected_results)
    raw_cache_file_sha = digest(transcript_path.read_bytes()) if transcript_path and transcript_path.exists() else None
    match_started = time.perf_counter()
    matched = match_units(units, transcript)
    if args.dialogue_docx:
        dialogues, warnings = add_groups(matched["units"], groups) if groups else ([], ["dialogue_groups_not_provided"])
    else:
        dialogues, warnings = script_dialogue_groups(matched["units"]), []
    if matched["unused_asr_tokens"]:
        warnings.append("unmatched_asr_content_requires_review")
    if any(r.get("kind") == "dialogue" and not r.get("speaker") for r in matched["units"]):
        warnings.append("dialogue_speakers_not_provided: determine from script, never infer from ASR")
    anchors = []
    by_id = {r["id"]: r for r in matched["units"]}
    for anchor in requested_anchors:
        row = by_id.get(anchor["unit_id"])
        if row is None:
            warnings.append(f"anchor_{anchor['id']}: unit id absent")
            continue
        anchors.append({**anchor, "script_text": row["text"], "estimated_start": row["estimated_start"],
            "estimated_end": row["estimated_end"], "issues": row["issues"], "boundary_status": "not_playback_verified"})
    reference_comparison = evaluate_reference(dialogues, anchors, matched, reference,
        source_hashes[str(args.audio.absolute())], [a["id"] for a in requested_anchors])
    source_content_hashes = {label: source_hashes[str(path.absolute())] for label, path in
        [("script", args.script), ("dialogue_docx", args.dialogue_docx), ("anchors", args.anchors_json)] if path}
    candidate = make_candidate(source_hashes[str(args.audio.absolute())], digest(pcm),
        len(pcm) / 32000, matched, dialogues, anchors, requested_anchors, warnings, source_content_hashes)
    candidate_confirmation = evaluate_adoption(candidate, confirmation, internal_review, mode_record)
    adoption = reference_comparison if reference is not None else candidate_confirmation
    match_seconds = time.perf_counter() - match_started
    # Check resolved paths and hard links before opening any generated WAV.
    clip_outputs = [output / "review_clips" / (re.sub(r"[^a-zA-Z0-9_-]", "_", p["id"]) + ".wav")
                    for p in dialogues + anchors]
    ensure_no_collisions(clip_outputs, protected_results)
    clips = write_clips(pcm, dialogues + anchors, output)
    timing.update(decode_seconds=decode_seconds, matching_seconds=match_seconds,
                  total_seconds=time.perf_counter() - started)
    if timing["total_seconds"] > 120:
        warnings.append("processing_exceeds_120_seconds: investigate timed stages")
    if any(digest(p.read_bytes()) != source_hashes[str(p.absolute())] for p in inputs):
        raise ValueError("An input changed during processing; do not treat this result as validated")
    if raw_cache_file_sha is not None and digest(transcript_path.read_bytes()) != raw_cache_file_sha:
        raise ValueError("Raw transcription cache changed during matching; do not treat this result as validated")
    result = dict(audio_file_sha256=source_hashes[str(args.audio.absolute())], decoded_pcm_sha256=digest(pcm),
        input_hashes=source_hashes, inputs_unchanged=True,
        decoded_duration_seconds=len(pcm) / 32000, source_origin_seconds=0,
        decoder_version=decoder_version, script_sha256=digest(args.script.read_bytes()),
        raw_transcript_sha256=transcript_sha(transcript), raw_transcript_cache_unchanged=True,
        matching=matched, dialogue_groups=dialogues, anchors=anchors, review_clips=clips,
        warnings=warnings, timing=timing, automatic_pass=adoption["automatic_pass"],
        adoption_status=adoption["adoption_status"], reference_comparison=reference_comparison,
        candidate=candidate, candidate_content_sha256=transcript_sha(candidate),
        candidate_confirmation=candidate_confirmation,
        audio_content_identity_sha256=audio_content_identity(candidate),
        derived_anchors_sha256=derived_anchors_identity(candidate),
        sentence_candidates=matched["units"],
        internal_review=candidate_confirmation["internal_review"],
        adoption_source=("user_reference_times" if reference is not None and adoption["automatic_pass"]
                         else candidate_confirmation["adoption_source"] if reference is None else None),
        scheme_approval=(candidate_confirmation["scheme_approval"] if reference is None
                         else dict(approved=False, source=None)),
        production_mode=(candidate_confirmation["production_mode"] if reference is None else "legacy_reference"),
        generation_status="not_evaluated", finished_video_evaluation="not_evaluated",
        playback_verified=False, measured_boundary_error_seconds=None,
        validation=("user_reference_tolerance_2s; playback_truth_unverified" if reference is not None
                    else "bound_content_review_and_adoption_source; no_independent_timing_reference; playback_truth_unverified"))
    save(output / "result.json", result, protected_results)
    if reference is not None:
        status = ("采用通过：全部用户参考边界差不超过2秒。尚未实际听检；参考差不等于实测误差。" if adoption["automatic_pass"]
                  else "采用未通过：" + ", ".join(adoption["blockers"]) + "。尚未实际听检。")
    elif adoption["automatic_pass"]:
        status = ("采用通过：已授权常规模式下GPT内部核查采用；不记用户方案认可。" if adoption["adoption_source"] == "gpt_internal_review"
                  else "采用通过：GPT核查完成且用户一次集中方案确认包含这份音频候选。") + "无独立参考时码，不声称满足2秒参考差；听检未做。"
    elif adoption["simulated_adoption_pass"]:
        status = "测试演练：模拟整体确认条件通过，真实用户未采用，automatic_pass仍为false。无独立参考时码；听检未做。"
    elif adoption["blockers"]:
        status = "候选暂不能采用：" + ", ".join(adoption["blockers"]) + "。听检未做。"
    else:
        status = "候选尚未确认；没有用户明确回复，不自动采用。无独立参考时码；听检未做。"
    lines = ["# 本机音频定位复核", "", status + "原台词以剧本为准。", "",
             f"原文件长度（解码）：{result['decoded_duration_seconds']:.4f} 秒。", ""]
    if reference is None:
        lines.extend([f"候选摘要：{len(matched['units'])}句段、{len(dialogues)}组对白、{len(anchors)}个当前派生段首。原句、说话者与直接听者来自GPT核定的剧本输入。GPT先处理内容／归属／边界疑点；验证模式随导演解读、画面和分段集中交用户一次整体确认。无需用户填写JSON或整套时码；沉默不算确认。常规模式只在已有真实落盘授权后内部采用。", "",
            f"完整候选内容指纹：`{result['candidate_content_sha256']}`。", ""])
        if args.candidate_confirmation_json is None:
            save(request_path, dict(basis="user_explicit", confirmed=False,
                audio_file_sha256=result["audio_file_sha256"],
                audio_content_identity_sha256=result["audio_content_identity_sha256"],
                derived_anchors_sha256=result["derived_anchors_sha256"], confirmation_note=""), protected_results)
        if args.internal_review_json is None:
            save(internal_request, dict(basis="gpt_internal_review", checked=False, project_scope="",
                audio_file_sha256=result["audio_file_sha256"],
                audio_content_identity_sha256=result["audio_content_identity_sha256"],
                derived_anchors_sha256=result["derived_anchors_sha256"],
                checks=dict(content_complete=False, roles_verified=False, boundaries_verified=False),
                reviewed_unit_ids=[], unresolved_blockers=candidate_blockers(candidate),
                review_source="", review_note=""), protected_results)
    lines.extend(["| 句段 | 归属 | 说话者 → 直接听者 | 原句 | 原文件估计区间／秒 | 疑点 |",
                  "|---|---|---|---|---|---|"])
    for row in matched["units"]:
        interval = "未确定" if row["estimated_start"] is None else f"{row['estimated_start']:.2f}–{row['estimated_end']:.2f}"
        listener = row.get("listeners", row.get("listener")) or "—"
        if isinstance(listener, list):
            listener = ", ".join(listener)
        text = row["text"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {row['id']} | {row.get('kind', '未核定')} | {row.get('speaker') or '旁白／未核定'} → {listener} | {text} | {interval} | {', '.join(row['issues']) or '听检未做'} |")
    lines.append("")
    lines.extend(["| 标记 | 原文件估计区间／秒 | " + ("用户参考最大差／秒" if reference is not None else "采用状态") + " | 疑点 |",
                  "|---|---|---|---|"])
    comparisons = {p["id"]: p for p in adoption["comparison_points"]}
    for point in dialogues + anchors:
        interval = "未确定" if point["estimated_start"] is None else f"{point['estimated_start']:.2f}–{point['estimated_end']:.2f}"
        comparison = comparisons.get(point["id"])
        difference = (f"{comparison['maximum_absolute_difference_seconds']:.2f}" if comparison else "参考未提供或无效") if reference is not None else adoption["adoption_status"]
        lines.append(f"| {point['id']} | {interval} | {difference} | {', '.join(point['issues']) or '听检未做'} |")
    lines.extend(["", "短段均保留原文件原点映射；用以下链接一次核对词首、词尾和对白归属。", ""])
    for clip in clips:
        lines.append(f"- [{clip['id']}]({clip['path']})：原文件 {clip['source_offset_seconds']:.2f}–{clip['source_end_seconds']:.2f} 秒。")
        point = next(p for p in dialogues + anchors if p["id"] == clip["id"])
        ids = point.get("unit_ids", [point.get("unit_id")])
        for identifier in ids:
            if identifier in by_id:
                row = by_id[identifier]
                speaker = row.get("speaker") or ("旁白（依剧本）" if row.get("kind") == "narration" else "说话者未知，按剧本核定")
                lines.append(f"  - {speaker}：{row['text']}")
    if matched["unused_asr_tokens"]:
        lines.extend(["", "未与本集正文配对的 ASR 内容（是否片头／误识别须播放判断）：", ""])
        for word in matched["unused_asr_tokens"]:
            lines.append(f"- {word['start']:.2f}–{word['end']:.2f} 秒：`{word['token']}`。")
    pending = [r for r in matched["units"] if r["issues"] and r.get("kind") == "dialogue"]
    if pending:
        lines.extend(["", "可选精检提示：" if not adoption["blockers"] else "需处理的对白疑点：", ""])
        for row in pending:
            lines.append(f"- {row['id']}：{row['text']}；{', '.join(row['issues'])}。")
    (output / "review.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(dict(result_path=str(output / "result.json"),
        review_path=str(output / "review.md"), timing=timing, warnings=warnings,
        automatic_pass=adoption["automatic_pass"], adoption_status=adoption["adoption_status"],
        maximum_reference_difference_seconds=reference_comparison["maximum_absolute_difference_seconds"],
        candidate_content_sha256=result["candidate_content_sha256"],
        audio_content_identity_sha256=result["audio_content_identity_sha256"],
        derived_anchors_sha256=result["derived_anchors_sha256"],
        adoption_source=result["adoption_source"], production_mode=result["production_mode"],
        simulated_adoption_pass=candidate_confirmation["simulated_adoption_pass"],
        confirmation_request_path=str(request_path) if reference is None and args.candidate_confirmation_json is None else None,
        internal_review_request_path=str(internal_request) if reference is None and args.internal_review_json is None else None), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, ImportError) as error:
        raise SystemExit(str(error))
