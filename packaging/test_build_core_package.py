"""Candidate builds must leave the recommended release and old artifacts alone."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_core_package as builder


class MetadataRoutingTests(unittest.TestCase):
    def test_asset_prompt_cannot_leak_a_local_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ASSET_DOWNLOAD_PROMPT.txt").write_text("/Users/private/project", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "absolute local path"):
                builder.validate_package(root)

    def test_status_routes(self):
        self.assertEqual(builder.metadata_filename("release"), "latest.json")
        for status in ("local_candidate", "branch_candidate"):
            self.assertEqual(builder.metadata_filename(status), "candidate.json")
        with self.assertRaises(ValueError):
            builder.metadata_filename("relase")

    def test_candidate_build_preserves_release_bytes_and_rebuilds_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg, releases = root / "packaging", root / "releases"
            pkg.mkdir()
            releases.mkdir()
            (pkg / "CORE_PACKAGE_README.md").write_text("# Fixture\n", encoding="utf-8")
            (pkg / "CHANGELOG.md").write_text("# Changes\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
            template = "memories/seedance_workflow/projects/PROJECT_TEMPLATE.md"
            (root / template).parent.mkdir(parents=True)
            (root / template).write_text("# Template\n", encoding="utf-8")
            config = dict(package_name="Fixture", version="1.8.0", release_date="2026-10-17",
                          update_policy="manual", summary="Candidate", release_status="local_candidate")
            (pkg / "package_config.json").write_text(json.dumps(config), encoding="utf-8")
            original = b'{"version":"1.7.3","release_status":"release"}\n'
            (releases / "latest.json").write_bytes(original)
            (releases / "old.zip").write_bytes(b"keep previous release")
            with patch.multiple(builder, REPO_ROOT=root, PACKAGING_DIR=pkg,
                                RELEASES_DIR=releases, CORE_FILES=["AGENTS.md", template]):
                with contextlib.redirect_stdout(io.StringIO()):
                    builder.main()
                    first = json.loads((releases / "candidate.json").read_text())
                    builder.main()
                second = json.loads((releases / "candidate.json").read_text())
                self.assertEqual(first, second)
                self.assertEqual(second["version"], "1.8.0")
                self.assertEqual(second["release_status"], "local_candidate")
                self.assertEqual((releases / "latest.json").read_bytes(), original)
                self.assertEqual((releases / "old.zip").read_bytes(), b"keep previous release")
                candidate_bytes = (releases / first["archive"]).read_bytes()
                config["release_status"] = "release"
                config["archive_suffix"] = "_release"
                (pkg / "package_config.json").write_text(json.dumps(config), encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    builder.main()
                published = json.loads((releases / "latest.json").read_text())
                self.assertEqual(published["release_status"], "release")
                self.assertNotEqual(published["archive"], first["archive"])
                self.assertEqual((releases / first["archive"]).read_bytes(), candidate_bytes)


if __name__ == "__main__":
    unittest.main()
