"""Preparation recovery and provenance checks; Windows execution remains a real-machine gate."""
import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bootstrap
import localize


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="bootstrap 中文 空格 ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.spec = bootstrap.platform_spec("Windows", "AMD64")
        self.stderr = redirect_stderr(io.StringIO())
        self.stderr.__enter__()
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def info(self, executable, isolated=True):
        return dict(executable=str(executable), version=[3, 12, 14], system="Windows",
                    machine="AMD64", bits=64, prefix=str(Path(executable).parent.parent),
                    base_prefix="C:/CPython312" if isolated else str(Path(executable).parent.parent))

    def test_platform_specific_locks_and_no_unsupported_fallback(self):
        self.assertEqual(self.spec["backend"], "faster-whisper")
        self.assertTrue(self.spec["lock"].endswith("windows-x64-py312.txt"))
        self.assertEqual(bootstrap.platform_spec("Darwin", "arm64")["backend"], "mlx")
        for system, machine in [("Windows", "ARM64"), ("Linux", "x86_64"), ("Darwin", "x86_64")]:
            with self.subTest(system=system, machine=machine), self.assertRaises(bootstrap.PreparationError):
                bootstrap.platform_spec(system, machine)

    def test_python_probe_keeps_unicode_space_argument_and_rejects_wrong_runtime(self):
        executable = str(self.root / "独立 Python/python.exe")
        data = self.info(executable)
        with patch.object(bootstrap, "run_command", return_value=subprocess.CompletedProcess([], 0, json.dumps(data), "")) as run:
            result = bootstrap.probe_python([executable], self.spec)
        self.assertEqual(result["executable"], executable)
        self.assertEqual(run.call_args.args[0][0], executable)
        self.assertIn("-I", run.call_args.args[0])
        data["version"] = [3, 13, 0]
        with patch.object(bootstrap, "run_command", return_value=subprocess.CompletedProcess([], 0, json.dumps(data), "")):
            self.assertIsNone(bootstrap.probe_python([executable], self.spec))

    def test_subprocess_is_utf8_argv_without_shell_or_path_mutation(self):
        arguments = [str(self.root / "Python 空格/python.exe"), "-m", "pip", "-r", str(self.root / "中文 lock.txt")]
        with patch.dict(bootstrap.os.environ, {"PYTHONPATH": "unexpected", "PIP_TARGET": "outside-venv"}), \
             patch.object(bootstrap.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            bootstrap.run_command(arguments)
        self.assertEqual(run.call_args.args[0], arguments)
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertEqual(run.call_args.kwargs["env"]["PYTHONUTF8"], "1")
        self.assertNotIn("PIP_TARGET", run.call_args.kwargs["env"])
        self.assertNotIn("PYTHONPATH", run.call_args.kwargs["env"])
        self.assertEqual(run.call_args.kwargs["env"]["PIP_CONFIG_FILE"], bootstrap.os.devnull)

    def test_busy_state_replace_preserves_old_utf8_state_then_retries(self):
        destination = self.root / "状态.json"
        bootstrap.atomic_json(destination, {"阶段": "已完成"})
        original = destination.read_bytes()
        real_replace = bootstrap.os.replace
        calls = []
        def transient(source, target):
            calls.append(target)
            if len(calls) == 1:
                raise PermissionError("sharing violation")
            return real_replace(source, target)
        with patch.object(bootstrap.os, "replace", side_effect=transient), patch.object(bootstrap.time, "sleep"):
            bootstrap.atomic_json(destination, {"阶段": "恢复完成"})
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["阶段"], "恢复完成")
        self.assertEqual(len(calls), 2)
        bootstrap.atomic_json(destination, {"阶段": "已完成"})
        with patch.object(bootstrap.os, "replace", side_effect=PermissionError("busy")), patch.object(bootstrap.time, "sleep"):
            with self.assertRaisesRegex(bootstrap.PreparationError, "旧文件已保留"):
                bootstrap.atomic_json(destination, {"阶段": "不可写"})
        self.assertEqual(destination.read_bytes(), original)
        self.assertFalse(list(self.root.glob("*.tmp")))

    def test_os_lock_blocks_duplicate_installer_and_releases(self):
        with bootstrap.state_lock(self.root):
            with self.assertRaisesRegex(bootstrap.PreparationError, "正在运行"):
                with bootstrap.state_lock(self.root):
                    self.fail("duplicate acquired lock")
        with bootstrap.state_lock(self.root):
            pass

    def test_interrupted_stage_never_recovers_as_passed(self):
        state = bootstrap.State(self.root, self.spec)
        state.data["stages"]["install_dependencies"] = {"status": "running"}
        state.data["pending_venv"] = str(self.root / "未完成环境")
        state.save()
        resumed = bootstrap.State(self.root, self.spec)
        self.assertEqual(resumed.data["stages"]["install_dependencies"]["status"], "interrupted")
        self.assertEqual(resumed.data["pending_venv"], str(self.root / "未完成环境"))
        with self.assertRaises(KeyboardInterrupt):
            resumed.stage("fixed_model", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
        saved = json.loads(resumed.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "interrupted")
        self.assertEqual(saved["stages"]["fixed_model"]["status"], "interrupted")

    def test_healthy_environment_reused_even_with_install_flag(self):
        environment = self.root / "已有 健康环境"
        python = bootstrap.venv_python(environment, self.spec)
        args = bootstrap.parser().parse_args(["--install", "--venv", str(environment),
            "--state-root", str(self.root / "state"), "--cache", str(self.root / "cache")])
        health = dict(python=str(python), decoder={"status": "passed", "real_audio_validated": False})
        with patch.object(bootstrap, "platform_spec", return_value=self.spec), \
             patch.object(bootstrap, "probe_python", return_value=self.info(python)), \
             patch.object(bootstrap, "worker", return_value=health) as worker, \
             patch.object(bootstrap, "install_environment") as install:
            result = bootstrap.prepare(args)
        install.assert_not_called()
        worker.assert_called_once()
        self.assertTrue(result["ok"])
        self.assertEqual(result["python"], str(python))
        self.assertEqual(result["audio"]["status"], "not_requested")
        self.assertFalse(result["audio"]["real_audio_validated"])
        saved = json.loads(Path(result["state_file"]).read_text(encoding="utf-8"))
        self.assertEqual(saved["stages"]["environment"]["result"]["status"], "reused")
        self.assertEqual(saved["active_python"], str(python))

    def test_broken_environment_preserved_and_partial_install_resumes_same_sibling(self):
        target = self.root / "venv"
        target.mkdir()
        sentinel = target / "old-environment.txt"
        sentinel.write_text("保留", encoding="utf-8")
        state = bootstrap.State(self.root / "state", self.spec)
        created, installs = [], []
        def command(arguments, timeout=None):
            if arguments[2] == "venv":
                destination = Path(arguments[3])
                destination.mkdir()
                created.append(destination)
                python = bootstrap.venv_python(destination, self.spec)
                python.parent.mkdir(parents=True)
                python.touch()
                return subprocess.CompletedProcess(arguments, 0, "", "")
            installs.append(arguments)
            return subprocess.CompletedProcess(arguments, 1 if len(installs) == 1 else 0, "", "interrupted download")
        def probe(arguments, spec):
            return self.info(arguments[0]) if Path(arguments[0]).exists() else None
        with patch.object(bootstrap, "run_command", side_effect=command), patch.object(bootstrap, "probe_python", side_effect=probe):
            with self.assertRaisesRegex(bootstrap.PreparationError, "恢复缺项"):
                bootstrap.install_environment(state, self.spec, "C:/CPython312/python.exe", target, self.root / "cache")
            pending = state.data["pending_venv"]
            self.assertNotEqual(pending, str(target))
            result = bootstrap.install_environment(state, self.spec, "C:/CPython312/python.exe", target, self.root / "cache")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "保留")
        self.assertEqual(len(created), 1)
        self.assertEqual(len(installs), 2)
        self.assertEqual(result, str(bootstrap.venv_python(pending, self.spec)))
        self.assertEqual(installs[0][0], installs[1][0])
        self.assertIn("--only-binary=:all:", installs[0])

    def test_explicit_old_venv_reuses_its_adopted_healthy_repair(self):
        old = self.root / "venv"
        repaired = self.root / "venv-repair-success"
        repaired_python = bootstrap.venv_python(repaired, self.spec)
        state_root = self.root / "state"
        state = bootstrap.State(state_root, self.spec)
        state.data.update(active_target=str(old), active_python=str(repaired_python))
        state.save()
        args = bootstrap.parser().parse_args(["--install", "--venv", str(old), "--state-root", str(state_root)])
        with patch.object(bootstrap, "platform_spec", return_value=self.spec), \
             patch.object(bootstrap, "probe_python", side_effect=lambda command, spec: self.info(command[0])), \
             patch.object(bootstrap, "worker", return_value={"python": str(repaired_python), "decoder": {}}) as worker, \
             patch.object(bootstrap, "install_environment") as install:
            result = bootstrap.prepare(args)
        self.assertEqual(result["python"], str(repaired_python))
        self.assertEqual(worker.call_args.args[0], str(repaired_python))
        install.assert_not_called()

    def test_missing_python_returns_codex_action_without_installing(self):
        args = bootstrap.parser().parse_args(["--install", "--state-root", str(self.root / "state"), "--cache", str(self.root / "cache")])
        with patch.object(bootstrap, "platform_spec", return_value=self.spec), \
             patch.object(bootstrap, "probe_python", return_value=None), \
             patch.object(bootstrap, "python_commands", return_value=[["missing-python"]]), \
             patch.object(bootstrap, "install_environment") as install:
            with self.assertRaises(bootstrap.PreparationError) as caught:
                bootstrap.prepare(args)
        install.assert_not_called()
        self.assertEqual(caught.exception.details["required_python"], "3.12")
        self.assertIn("Codex", str(caught.exception))
        self.assertIn("python.org", caught.exception.details["official_source"])
        saved = json.loads((self.root / "state/bootstrap-state.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["stages"]["python_runtime"]["status"], "failed")

    def test_decoder_generated_probe_never_sent_to_asr_or_adopted(self):
        visited = []
        def decode(source):
            visited.append(source)
            self.assertTrue(source.is_file())
            self.assertIn("声音 自检", str(source))
            return b"\x00\x00" * 1600, "bundled decoder"
        with patch.dict("sys.modules", {"imageio_ffmpeg": SimpleNamespace(get_ffmpeg_exe=lambda: "bundled-decoder")}), \
             patch.object(localize, "decode", side_effect=decode), \
             patch.object(localize, "get_transcript", side_effect=AssertionError("synthetic ASR forbidden")) as transcribe:
            result = bootstrap.decoder_smoke()
        transcribe.assert_not_called()
        self.assertFalse(visited[0].exists())
        self.assertTrue(result["generated_test_signal"])
        self.assertFalse(result["real_audio_validated"])

    def test_real_audio_cache_and_inference_remain_distinct_from_adoption(self):
        source = self.root / "真实 原音轨.wav"
        source.write_bytes(b"actual input test fixture")
        transcript = {"segments": [{"words": [{"word": "hello", "start": 0, "end": .1}]}]}
        for hit in (False, True):
            with self.subTest(cache_hit=hit), patch.object(localize, "decode", return_value=(b"\0\0" * 1600, "decoder")), \
                 patch.object(localize, "get_transcript", return_value=(transcript, {"transcript_cache_hit": hit})) as transcribe:
                result = bootstrap.check_audio("faster-whisper", self.root / "cache", source, False)
            self.assertEqual(result["inference_executed"], not hit)
            self.assertEqual(result["status"], "cache_reused" if hit else "transcribed")
            self.assertEqual(result["production_adoption"], "not_evaluated")
            self.assertFalse(result["listening_verified"])
            self.assertEqual(transcribe.call_args.kwargs["protected"], [source])
            self.assertEqual(transcribe.call_args.kwargs["backend"], "faster-whisper")
        self.assertEqual(source.read_bytes(), b"actual input test fixture")

    def test_audio_changed_during_check_cannot_be_reported_successful(self):
        source = self.root / "真实.wav"
        source.write_bytes(b"original")
        def changed(*args, **kwargs):
            source.write_bytes(b"changed concurrently")
            return {"segments": []}, {"transcript_cache_hit": False}
        with patch.object(localize, "decode", return_value=(b"\0\0" * 1600, "decoder")), \
             patch.object(localize, "get_transcript", side_effect=changed), \
             self.assertRaisesRegex(bootstrap.PreparationError, "发生变化"):
            bootstrap.check_audio("faster-whisper", self.root / "cache", source, False)

    def test_windows_runtime_probe_imports_cpu_only_and_checks_int8(self):
        imported = []
        def module(name):
            imported.append(name)
            return SimpleNamespace(get_supported_compute_types=lambda device: {"int8", "float32"})
        with patch.object(bootstrap, "platform_spec", return_value=self.spec), \
             patch.object(bootstrap, "package_versions", return_value={"faster-whisper": "locked"}), \
             patch.object(bootstrap.importlib, "import_module", side_effect=module), \
             patch.object(bootstrap, "decoder_smoke", return_value={"status": "passed"}):
            result = bootstrap.runtime_health("faster-whisper")
        self.assertNotIn("mlx", imported)
        self.assertNotIn("mlx_whisper", imported)
        self.assertEqual(result["execution"]["compute_type"], "int8")
        self.assertFalse(result["real_audio_validated"])
        self.assertFalse(result["execution"]["real_model_inference"])

    def test_windows_dll_failure_provides_system_authorization_step(self):
        args = argparse.Namespace(_worker="runtime", _backend="faster-whisper", cache=self.root)
        output = io.StringIO()
        with patch.object(bootstrap, "runtime_health", side_effect=ImportError("DLL load failed: WinError 126")), \
             patch.object(bootstrap.platform, "system", return_value="Windows"), \
             patch.dict(bootstrap.os.environ), redirect_stdout(output):
            code = bootstrap.run_worker(args)
        record = json.loads(output.getvalue().strip().removeprefix(bootstrap.MARKER))
        self.assertEqual(code, 1)
        self.assertIn("正常授权", record["details"]["system_action"])
        self.assertEqual(record["details"]["official_source"], "https://aka.ms/vs/17/release/vc_redist.x64.exe")
        self.assertFalse(record["ok"])

    def test_missing_real_audio_does_not_create_or_claim_ready_state(self):
        state = self.root / "state"
        args = bootstrap.parser().parse_args(["--audio", str(self.root / "missing.wav"), "--state-root", str(state)])
        with patch.object(bootstrap, "platform_spec", return_value=self.spec), self.assertRaises(bootstrap.PreparationError):
            bootstrap.prepare(args)
        self.assertFalse(state.exists())

    def test_audio_alias_to_state_is_rejected_before_any_state_write(self):
        state = self.root / "state"
        state.mkdir()
        existing = state / "bootstrap-state.json"
        existing.write_bytes(b"original audio bytes")
        audio_alias = self.root / "alias.wav"
        bootstrap.os.link(existing, audio_alias)
        args = bootstrap.parser().parse_args(["--audio", str(audio_alias), "--state-root", str(state)])
        with patch.object(bootstrap, "platform_spec", return_value=self.spec), self.assertRaisesRegex(bootstrap.PreparationError, "碰撞"):
            bootstrap.prepare(args)
        self.assertEqual(existing.read_bytes(), b"original audio bytes")
        self.assertFalse((state / ".bootstrap.lock").exists())


if __name__ == "__main__":
    unittest.main()
