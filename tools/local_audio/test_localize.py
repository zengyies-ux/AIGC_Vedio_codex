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


class UserReferenceTests(unittest.TestCase):
    def fixture(self, heard="Stay with me."):
        units = [{"id": "u1", "text": '"Stay with me."', "kind": "dialogue", "speaker": "script_actor"}]
        matched = localize.match_units(units, transcript(heard))
        groups, _ = localize.add_groups(matched["units"], [['"Stay with me."']])
        row = matched["units"][0]
        anchors = [dict(id="anchor_A", unit_id="u1", estimated_start=row["estimated_start"], estimated_end=row["estimated_end"])]
        reference = dict(basis="user_supplied", audio_file_sha256="a" * 64, tolerance_seconds=2,
            dialogue_groups={"dialogue_01": {"start": 2.0, "end": 2.75}},
            anchors={"anchor_A": {"start": 2.0}})
        return groups, anchors, matched, reference

    def evaluate(self, fixture):
        groups, anchors, matched, reference = fixture
        return localize.evaluate_reference(groups, anchors, matched, reference, "a" * 64, ["anchor_A"])

    def test_exactly_two_seconds_passes_without_claiming_playback_truth(self):
        result = self.evaluate(self.fixture())
        self.assertTrue(result["automatic_pass"])
        self.assertEqual(result["maximum_absolute_difference_seconds"], 2)
        self.assertEqual(result["adoption_status"], "user_reference_passed")
        self.assertFalse(result["playback_verified"])
        self.assertIsNone(result["measured_boundary_error_seconds"])

    def test_more_than_two_seconds_does_not_pass(self):
        fixture = self.fixture()
        fixture[3]["anchors"]["anchor_A"]["start"] = 2.01
        result = self.evaluate(fixture)
        self.assertFalse(result["automatic_pass"])
        self.assertIn("anchor_A:reference_difference_exceeds_2_seconds", result["blockers"])

    def test_missing_invalid_or_incomplete_references_do_not_pass(self):
        for mutation in ["endpoint", "anchor", "nan", "tolerance"]:
            with self.subTest(mutation=mutation):
                fixture = self.fixture()
                reference = fixture[3]
                if mutation == "endpoint":
                    del reference["dialogue_groups"]["dialogue_01"]["end"]
                elif mutation == "anchor":
                    reference["anchors"] = {}
                elif mutation == "nan":
                    reference["anchors"]["anchor_A"]["start"] = float("nan")
                else:
                    del reference["tolerance_seconds"]
                self.assertFalse(self.evaluate(fixture)["automatic_pass"])
        groups, anchors, matched, _ = self.fixture()
        self.assertFalse(localize.evaluate_reference(groups, anchors, matched, None, "a" * 64)["automatic_pass"])

    def test_reference_from_different_audio_does_not_pass(self):
        fixture = self.fixture()
        fixture[3]["audio_file_sha256"] = "b" * 64
        result = self.evaluate(fixture)
        self.assertFalse(result["automatic_pass"])
        self.assertIn("reference_audio_fingerprint_mismatch", result["blockers"])

    def test_reference_tolerance_cannot_mask_missing_words_or_ambiguous_repeat(self):
        fixture = self.fixture("Stay with")
        result = self.evaluate(fixture)
        self.assertFalse(result["automatic_pass"])
        self.assertIn("script_alignment_incomplete", result["blockers"])
        fixture = self.fixture()
        fixture[2]["units"][0]["issues"].append("ambiguous_repeat")
        result = self.evaluate(fixture)
        self.assertFalse(result["automatic_pass"])
        self.assertIn("u1:ambiguous_repeat", result["blockers"])

    def test_prefix_extra_warns_but_unmatched_body_content_blocks(self):
        prefix = self.fixture("Title. Stay with me.")
        row = prefix[2]["units"][0]
        prefix[3]["dialogue_groups"]["dialogue_01"] = {"start": row["estimated_start"], "end": row["estimated_end"]}
        prefix[3]["anchors"]["anchor_A"]["start"] = row["estimated_start"]
        self.assertTrue(self.evaluate(prefix)["automatic_pass"])
        body = self.fixture("Stay really with me.")
        result = self.evaluate(body)
        self.assertFalse(result["automatic_pass"])
        self.assertIn("unmatched_asr_inside_script_body", result["blockers"])

    def test_duplicate_reference_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as directory:
            path = Path(directory) / "reference.json"
            path.write_text('{"anchors": {}, "anchors": {}}')
            with self.assertRaisesRegex(ValueError, "Duplicate reference key"):
                localize.read_reference(path)


class CandidateConfirmationTests(unittest.TestCase):
    def fixture(self, heard="Stay with me."):
        groups, anchors, matched, _ = UserReferenceTests().fixture(heard)
        candidate = localize.make_candidate("a" * 64, "b" * 64, 2, matched, groups, anchors,
            [{"id": "anchor_A", "unit_id": "u1"}], [], {"script": "c" * 64})
        confirmation = dict(basis="user_explicit", confirmed=True,
            audio_file_sha256="a" * 64, candidate_content_sha256=localize.transcript_sha(candidate),
            confirmation_note="Synthetic test reply: adopt these candidates.")
        return candidate, confirmation

    def test_silence_and_template_do_not_adopt_or_claim_two_second_reference(self):
        candidate, confirmation = self.fixture()
        result = localize.evaluate_confirmation(candidate, None)
        self.assertFalse(result["automatic_pass"])
        self.assertEqual(result["adoption_status"], "candidate_pending_user_confirmation")
        self.assertIsNone(result["maximum_absolute_difference_seconds"])
        self.assertEqual(result["comparison_points"], [])
        confirmation["confirmed"] = False
        self.assertFalse(localize.evaluate_confirmation(candidate, confirmation)["automatic_pass"])

    def test_user_confirmation_requires_nonblank_reply_record(self):
        for note in [None, "", " \t\n", 42, False]:
            with self.subTest(note=note):
                candidate, confirmation = self.fixture()
                if note is None:
                    del confirmation["confirmation_note"]
                else:
                    confirmation["confirmation_note"] = note
                result = localize.evaluate_confirmation(candidate, confirmation)
                self.assertIn("confirmation_reply_missing", result["blockers"])
                self.assertFalse(result["automatic_pass"])
                self.assertFalse(result["user_confirmation_recorded"])
                self.assertIsNone(result["confirmation_fact"])

    def test_explicit_reply_records_fact_without_claiming_playback(self):
        candidate, confirmation = self.fixture()
        result = localize.evaluate_confirmation(candidate, confirmation)
        self.assertTrue(result["automatic_pass"])
        self.assertEqual(result["adoption_status"], "user_confirmed_candidates")
        self.assertTrue(result["user_confirmation_recorded"])
        self.assertEqual(result["confirmation_fact"]["confirmation_note"], confirmation["confirmation_note"])
        self.assertIn("recorded_at_utc", result["confirmation_fact"])
        self.assertFalse(result["playback_verified"])
        self.assertIsNone(result["measured_boundary_error_seconds"])
        self.assertIsNone(result["maximum_absolute_difference_seconds"])

    def test_simulation_cannot_become_real_user_adoption(self):
        candidate, confirmation = self.fixture()
        confirmation["basis"] = "test_simulation"
        result = localize.evaluate_confirmation(candidate, confirmation)
        self.assertFalse(result["automatic_pass"])
        self.assertFalse(result["user_confirmation_recorded"])
        self.assertTrue(result["simulated_adoption_pass"])
        self.assertEqual(result["adoption_status"], "candidate_confirmation_simulated")
        self.assertEqual(result["confirmation_fact"]["basis"], "test_simulation")

    def test_wrong_audio_missing_hash_and_nonaffirmative_reply_are_rejected(self):
        for mutation in ["audio", "candidate", "missing_hash", "string_true", "basis"]:
            with self.subTest(mutation=mutation):
                candidate, confirmation = self.fixture()
                if mutation == "audio":
                    confirmation["audio_file_sha256"] = "d" * 64
                elif mutation == "candidate":
                    confirmation["candidate_content_sha256"] = "d" * 64
                elif mutation == "missing_hash":
                    del confirmation["candidate_content_sha256"]
                elif mutation == "string_true":
                    confirmation["confirmed"] = "true"
                else:
                    confirmation["basis"] = "silence"
                result = localize.evaluate_confirmation(candidate, confirmation)
                self.assertFalse(result["automatic_pass"])
                self.assertFalse(result["user_confirmation_recorded"])

    def test_confirmation_expires_when_any_candidate_content_changes(self):
        for section, field, value in [("matching", "text", '"Stay near me."'),
                ("matching", "speaker", "different_script_actor"),
                ("matching", "estimated_end", 1),
                ("dialogue_groups", "script_text", ['"Stay near me."']),
                ("anchors", "unit_id", "another_unit")]:
            with self.subTest(section=section, field=field):
                candidate, confirmation = self.fixture()
                row = candidate[section]["units"][0] if section == "matching" else candidate[section][0]
                row[field] = value
                result = localize.evaluate_confirmation(candidate, confirmation)
                self.assertFalse(result["automatic_pass"])
                self.assertIn("confirmation_candidate_fingerprint_mismatch", result["blockers"])

    def test_reply_cannot_hide_missing_text_unknown_speaker_or_missing_anchor(self):
        for mutation in ["missing_text", "speaker", "anchor", "repeat"]:
            with self.subTest(mutation=mutation):
                candidate, confirmation = self.fixture("Stay with" if mutation == "missing_text" else "Stay with me.")
                if mutation == "speaker":
                    candidate["matching"]["units"][0]["speaker"] = None
                elif mutation == "anchor":
                    candidate["anchors"] = []
                elif mutation == "repeat":
                    candidate["matching"]["units"][0]["issues"].append("ambiguous_repeat")
                confirmation["candidate_content_sha256"] = localize.transcript_sha(candidate)
                self.assertFalse(localize.evaluate_confirmation(candidate, confirmation)["automatic_pass"])

    def test_candidate_is_stable_and_independent_of_runtime_or_later_mutation(self):
        candidate, _ = self.fixture()
        groups, anchors, matched, _ = UserReferenceTests().fixture()
        copied = localize.make_candidate("a" * 64, "b" * 64, 2, matched, groups, anchors,
            [{"id": "anchor_A", "unit_id": "u1"}], [], {"script": "c" * 64})
        before = localize.transcript_sha(copied)
        matched["units"][0]["text"] = "changed after candidate snapshot"
        self.assertEqual(localize.transcript_sha(copied), before)
        self.assertEqual(before, localize.transcript_sha(candidate))

    def test_reference_and_confirmation_cannot_be_combined_before_decode(self):
        argv = ["localize.py", "--audio", "audio.wav", "--script", "script.json",
                "--reference-times-json", "reference.json", "--candidate-confirmation-json", "reply.json"]
        with patch.object(sys, "argv", argv), patch.object(localize, "decode") as decoder:
            with self.assertRaisesRegex(ValueError, "not both"):
                localize.main()
            decoder.assert_not_called()


if __name__ == "__main__":
    unittest.main()
