"""Meaningful failure cases for monotone matching and ASR cache reuse."""
import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch

import localize

TEST_TMP = Path(__file__).resolve().parents[2] / ".codex_tmp/audio_v3/test_tmp"
TEST_TMP.mkdir(parents=True, exist_ok=True)


def transcript(text):
    return {"text": text, "language": "en", "segments": [{"words": [{"word": w, "start": i * .25,
        "end": (i + 1) * .25, "probability": .99}
        for i, w in enumerate(text.split())]}]}


class MatchingTests(unittest.TestCase):
    def test_repeated_line_cannot_reuse_heard_words(self):
        units = [{"id": "a", "text": "Will you stay?"},
                 {"id": "b", "text": "Will you stay?"}]
        result = localize.match_units(units, transcript("Will you stay?"))
        self.assertEqual(sum(r["exact_tokens"] for r in result["units"]), 3)
        self.assertTrue(any(r["missing_tokens"] for r in result["units"]))
        self.assertEqual(result["script_tokens"], 6)
        self.assertTrue(all("ambiguous_repeat" in r["issues"] for r in result["units"]))

    def test_complete_repetitions_have_distinct_monotone_intervals(self):
        units = [{"id": "a", "text": "Will you stay?"},
                 {"id": "b", "text": "Will you stay?"}]
        result = localize.match_units(units, transcript("Will you stay? Will you stay?"))
        first, second = result["units"]
        self.assertNotIn("ambiguous_repeat", first["issues"])
        self.assertLessEqual(first["estimated_end"], second["estimated_start"])

    def test_verified_model_reuses_offline_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as directory:
            cache = Path(directory)
            model = cache / "model"
            model.mkdir()
            (model / "config.json").write_bytes(b"{}")
            (model / "weights.npz").write_bytes(b"test model")
            localize.save(model / "local_manifest.json", dict(model=localize.MODEL,
                revision=localize.REVISION, files={n: localize.digest((model / n).read_bytes())
                for n in ("config.json", "weights.npz")}))
            path, timing = localize.model_directory(cache)
            self.assertEqual(path, str(model))
            self.assertEqual(timing["model_download_seconds"], 0)
            (model / "weights.npz").write_bytes(b"changed model")
            with self.assertRaisesRegex(ValueError, "integrity failed"):
                localize.model_directory(cache)

    def test_deleted_dialogue_is_not_borrowed_from_later_response(self):
        units = [{"id": "n1", "text": "She paused at the door."},
                 {"id": "d", "text": '"Please stay with me."', "kind": "dialogue"},
                 {"id": "n2", "text": "He left the room."}]
        result = localize.match_units(units, transcript("She paused at the door. He left the room."))
        dialogue = result["units"][1]
        self.assertIsNone(dialogue["estimated_start"])
        self.assertIn("incomplete_boundary", dialogue["issues"])

    def test_partial_sentence_keeps_script_and_reports_lost_end(self):
        source = '"Are you certain about this?"'
        result = localize.match_units([{"id": "x", "text": source}], transcript("Are you certain about"))
        row = result["units"][0]
        self.assertEqual(row["text"], source)
        self.assertEqual(row["missing_tokens"], ["this"])
        self.assertIn("incomplete_boundary", row["issues"])
        self.assertEqual(row["boundary_status"], "not_playback_verified")

    def test_zero_duration_short_word_is_flagged(self):
        sample = {"segments": [{"words": [{"word": "I...", "start": 7, "end": 7}]}]}
        row = localize.match_units([{"id": "x", "text": '"I..."'}], sample)["units"][0]
        self.assertIn("zero_or_negative_estimated_duration", row["issues"])
        self.assertIn("short_phrase_requires_context_review", row["issues"])

    def test_new_script_uses_same_transcript_without_importing_backend(self):
        pcm = b"\x01\x02" * 16000
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as directory:
            cache = Path(directory)
            settings = dict(format_version=localize.VERSION, pcm_sha256=localize.digest(pcm),
                pcm_format="16000 Hz mono s16le", model=localize.MODEL,
                revision=localize.REVISION, parameters=localize.PARAMS, tool_versions={"test": "1"})
            key = localize.digest(json.dumps(settings, sort_keys=True).encode())
            heard = transcript("She smiled. He stayed.")
            destination = cache / "transcripts" / (key + ".json")
            localize.save(destination, dict(settings=settings, transcript=heard,
                transcript_sha256=localize.transcript_sha(heard)))
            with patch.object(localize, "configured_versions", return_value={"test": "1"}):
                original, timing = localize.get_transcript(pcm, cache)
                revised, again = localize.get_transcript(pcm, cache)
            self.assertTrue(timing["transcript_cache_hit"])
            self.assertTrue(again["transcript_cache_hit"])
            a = localize.match_units([{"id": "a", "text": "She smiled."}], original)
            b = localize.match_units([{"id": "b", "text": "He stayed."}], revised)
            self.assertEqual(a["units"][0]["estimated_start"], 0)
            self.assertEqual(b["units"][0]["estimated_start"], .5)
            corrupted = json.loads(destination.read_text())
            corrupted["transcript"]["segments"][0]["words"][0]["start"] = .01
            localize.save(destination, corrupted)
            with patch.object(localize, "configured_versions", return_value={"test": "1"}):
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    localize.get_transcript(pcm, cache)

    def test_word_schema_rejects_nan_negative_and_nonmonotone_times(self):
        for value in [float("nan"), -1, 3]:
            result = transcript("She stayed")
            result["segments"][0]["words"][0]["start"] = value
            with self.assertRaises(ValueError):
                localize.validate_transcript(result, 2)
        result = transcript("She stayed")
        result["segments"][0]["words"][1]["start"] = .01
        result["segments"][0]["words"][1]["end"] = .1
        with self.assertRaisesRegex(ValueError, "Nonmonotone"):
            localize.validate_transcript(result, 2)

    def test_input_wav_at_clip_destination_is_rejected_before_decode(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as directory:
            root = Path(directory)
            clip = root / "out/review_clips/dialogue_01.wav"
            clip.parent.mkdir(parents=True)
            original = b"original audio; never overwritten"
            clip.write_bytes(original)
            script = root / "script.json"
            localize.save(script, {"units": [{"id": "x", "text": '"Stay."',
                "kind": "dialogue", "speaker": "from_script", "dialogue_group": "g1"}]})
            args = ["localize.py", "--audio", str(clip), "--script", str(script), "--out", str(root / "out")]
            with patch.object(sys, "argv", args), patch.object(localize, "decode") as decoder:
                with self.assertRaisesRegex(ValueError, "collision"):
                    localize.main()
                decoder.assert_not_called()
            self.assertEqual(clip.read_bytes(), original)

    def test_hardlinked_output_cannot_overwrite_input(self):
        import os
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as directory:
            source, output = Path(directory) / "audio.wav", Path(directory) / "clip.wav"
            source.write_bytes(b"audio")
            os.link(source, output)
            with self.assertRaisesRegex(ValueError, "collision"):
                localize.ensure_no_collisions([output], [source])

    def test_sanitized_clip_name_collision_is_rejected_before_decode(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as directory:
            root = Path(directory)
            audio = root / "input.wav"
            audio.write_bytes(b"original audio")
            script, anchors = root / "script.json", root / "anchors.json"
            localize.save(script, {"units": [{"id": "x", "text": "She stayed."}]})
            localize.save(anchors, [{"id": "a.b", "unit_id": "x"}, {"id": "a?b", "unit_id": "x"}])
            argv = ["localize.py", "--audio", str(audio), "--script", str(script),
                "--anchors-json", str(anchors), "--out", str(root / "out")]
            with patch.object(sys, "argv", argv), patch.object(localize, "decode") as decoder:
                with self.assertRaisesRegex(ValueError, "clip names"):
                    localize.main()
                decoder.assert_not_called()


if __name__ == "__main__":
    unittest.main()
