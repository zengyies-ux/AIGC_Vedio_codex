#!/usr/bin/env python3
"""Codex-operated local audio preparation. No system Python/PATH mutation.

Run with any available Python, then reuse a healthy isolated CPython 3.12 or
pass --install to create one beside an unhealthy environment. --prepare-model
verifies/downloads the pinned model; --audio checks an actual MP3/WAV. This
entry point never adopts audio candidates or performs browser operations.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import wave

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
MARKER = "SEEDANCE_BOOTSTRAP_RESULT="
PROBE = ("import json,platform,struct,sys; from pathlib import Path; "
         "cfg=Path(sys.prefix)/'pyvenv.cfg'; "
         "system_sites=any(line.split('=',1)[0].strip()=='include-system-site-packages' "
         "and line.split('=',1)[1].strip().lower()=='true' "
         "for line in cfg.read_text(encoding='utf-8').splitlines() if '=' in line) if cfg.exists() else False; "
         "print(json.dumps(dict("
         "executable=sys.executable,version=list(sys.version_info[:3]),"
         "system=platform.system(),machine=platform.machine(),bits=struct.calcsize('P')*8,"
         "prefix=sys.prefix,base_prefix=sys.base_prefix,"
         "system_site_packages=system_sites,"
         "base_executable=getattr(sys,'_base_executable',sys.executable))))")


class PreparationError(RuntimeError):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def absolute(path):
    # Resolving a venv's python symlink would accidentally select the base Python.
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def sha_file(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def platform_spec(system=None, machine=None):
    system, machine = system or platform.system(), (machine or platform.machine()).lower()
    if system == "Windows" and machine in ("amd64", "x86_64"):
        return dict(system=system, architecture="x64", backend="faster-whisper",
                    lock=str(HERE / "requirements-lock-windows-x64-py312.txt"))
    if system == "Darwin" and machine in ("arm64", "aarch64"):
        return dict(system=system, architecture="arm64", backend="mlx",
                    lock=str(HERE / "requirements-lock-macos-arm64-py312.txt"))
    raise PreparationError("当前候选仅支持 Apple silicon macOS 和 Windows x64 CPU。",
                           dict(system=system, machine=machine, windows_validation="pending_real_machine"))


def child_env():
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "PIP_TARGET", "PIP_PREFIX", "PIP_ROOT", "PIP_USER", "PIP_PYTHON"):
        env.pop(name, None)
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PIP_DISABLE_PIP_VERSION_CHECK="1",
               PYTHONNOUSERSITE="1", PIP_CONFIG_FILE=os.devnull, PIP_NO_INPUT="1",
               HF_HUB_DISABLE_TELEMETRY="1", HF_HUB_DISABLE_XET="1")
    return env


def run_command(arguments, timeout=None):
    return subprocess.run([str(arg) for arg in arguments], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=child_env(),
                          timeout=timeout, check=False)


def atomic_json(path, value):
    """Unique same-volume temporary file; retry Windows sharing violations."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(5):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 4:
                    raise PreparationError("状态文件被占用；旧文件已保留，释放占用后可重跑。",
                                           dict(path=str(path), retryable=True))
                time.sleep(.05 * (2 ** attempt))
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except PermissionError:
            # Antivirus may still hold the temporary file; never remove old state.
            pass


@contextmanager
def state_lock(root):
    """OS releases this lock on process exit, including interrupted installs."""
    root.mkdir(parents=True, exist_ok=True)
    stream = (root / ".bootstrap.lock").open("a+b")
    locked = False
    try:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as error:
            raise PreparationError("此环境准备任务正在运行；先读取当前状态，不要并发安装。",
                                   dict(state_root=str(root), retryable=True)) from error
        yield
    finally:
        try:
            if locked:
                if os.name == "nt":
                    import msvcrt
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()


class State:
    def __init__(self, root, spec):
        self.path = root / "bootstrap-state.json"
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise PreparationError("现有准备状态无法读取；保留原文件，使用另一个 --state-root 恢复。") from error
            if not isinstance(self.data, dict) or self.data.get("schema_version") != 1 or not isinstance(self.data.get("stages"), dict):
                raise PreparationError("现有准备状态格式无效；保留原文件，使用另一个 --state-root 恢复。")
        else:
            self.data = dict(schema_version=1, stages={})
        if self.data.get("platform") not in (None, spec):
            # State may have travelled with a project; do not reuse another platform's venv.
            self.data.pop("active_python", None)
            self.data.pop("active_target", None)
            self.data.pop("pending_venv", None)
            self.data.pop("pending_target", None)
        self.data["platform"] = spec
        for stage in self.data["stages"].values():
            if stage.get("status") == "running":
                stage.update(status="interrupted", interrupted_at=utc_now())
        self.data.update(status="running", updated_at=utc_now(), last_error=None)
        self.save()

    def save(self):
        self.data["updated_at"] = utc_now()
        atomic_json(self.path, self.data)

    def stage(self, name, operation):
        self.data["current_stage"] = name
        self.data["stages"][name] = dict(status="running", started_at=utc_now())
        self.save()
        print("本机音频准备：" + name, file=sys.stderr, flush=True)
        started = time.perf_counter()
        try:
            result = operation()
        except BaseException as error:
            details = getattr(error, "details", {})
            status = "interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed"
            self.data["stages"][name].update(status=status, finished_at=utc_now(),
                elapsed_seconds=time.perf_counter() - started, error=str(error), details=details)
            self.data.update(status=status, last_error=dict(stage=name, message=str(error), details=details))
            self.save()
            raise
        self.data["stages"][name].update(status="passed", finished_at=utc_now(),
            elapsed_seconds=time.perf_counter() - started, result=result)
        self.save()
        return result


def venv_python(directory, spec):
    return absolute(directory) / ("Scripts/python.exe" if spec["system"] == "Windows" else "bin/python")


def probe_python(command, spec):
    try:
        completed = run_command([*command, "-I", "-c", PROBE], timeout=20)
        if completed.returncode:
            return None
        result = json.loads(completed.stdout.strip())
        if (result["version"][:2] != [3, 12] or result["system"] != spec["system"]
                or result["bits"] != 64):
            return None
        arch = result["machine"].lower()
        if arch not in (("arm64", "aarch64") if spec["architecture"] == "arm64" else ("amd64", "x86_64")):
            return None
        return result
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        return None


def python_commands(explicit=None):
    if explicit:
        return [[str(absolute(explicit))]]
    commands = [[sys.executable]]
    base = getattr(sys, "_base_executable", None)
    if base:
        commands.append([base])
    if platform.system() == "Windows":
        launcher = shutil.which("py")
        if launcher:
            commands.append([launcher, "-3.12"])
        for parent in (os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles")):
            if parent:
                directory = Path(parent) / ("Programs/Python/Python312" if parent == os.environ.get("LOCALAPPDATA") else "Python312")
                commands.append([str(directory / "python.exe")])
    for name in ("python3.12", "python3", "python"):
        found = shutil.which(name)
        if found:
            commands.append([found])
    return list(dict.fromkeys(tuple(command) for command in commands))


def missing_python(spec):
    return PreparationError("未找到此平台的 64 位 CPython 3.12；由 Codex 准备官方运行时后重跑。",
        dict(required_python="3.12", system=spec["system"], architecture=spec["architecture"],
             codex_next_action="从 python.org 官方发行准备独立 CPython 3.12，再以 --python 绝对路径 --install 重跑；无需用户手配 venv、DLL 或 PATH。",
             official_source="https://www.python.org/downloads/windows/" if spec["system"] == "Windows" else "https://www.python.org/downloads/macos/"))


def worker(python, kind, spec, cache, audio=None, force=False):
    arguments = [python, HERE / "bootstrap.py", "--_worker", kind,
                 "--_backend", spec["backend"], "--cache", cache]
    if audio:
        arguments.extend(["--audio", audio])
    if force:
        arguments.append("--force-transcribe")
    completed = run_command(arguments)
    lines = [line[len(MARKER):] for line in completed.stdout.splitlines() if line.startswith(MARKER)]
    if not lines:
        raise PreparationError("隔离运行时未返回完整结果。", dict(returncode=completed.returncode,
                               stderr=completed.stderr[-3000:], retryable=True))
    result = json.loads(lines[-1])
    if completed.returncode or not result.get("ok"):
        raise PreparationError(result.get("error", "运行时检查失败。"), result.get("details", {}))
    return result["result"]


def package_versions(lock):
    expected = {}
    for line in Path(lock).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name, version = line.split("==")
            expected[name] = version
    actual, mismatches = {}, {}
    for name, version in expected.items():
        try:
            actual[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual[name] = None
        if actual[name] != version:
            mismatches[name] = dict(expected=version, actual=actual[name])
    if mismatches:
        raise PreparationError("隔离环境依赖与当前平台锁文件不一致。", dict(package_mismatches=mismatches))
    return actual


def decoder_smoke():
    """Synthetic silence checks decoding only. It is never sent to ASR."""
    from localize import decode
    import imageio_ffmpeg
    started = time.perf_counter()
    frames = b"\x00\x00" * 1600
    with tempfile.TemporaryDirectory(prefix="Seedance 声音 自检 ") as folder:
        source = Path(folder) / "短 音轨.wav"
        # Close wave handle before launching decoder (Windows sharing semantics).
        with wave.open(str(source), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(frames)
        pcm, version = decode(source)
    if pcm != frames:
        raise PreparationError("内置 decoder 未保持短 WAV 的完整 PCM。")
    return dict(status="passed", executable=imageio_ffmpeg.get_ffmpeg_exe(), version=version,
                seconds=time.perf_counter() - started, generated_test_signal=True,
                real_audio_validated=False)


def runtime_health(backend):
    spec = platform_spec()
    if backend != spec["backend"]:
        raise PreparationError("自检后端与实际平台不一致。")
    versions = package_versions(spec["lock"])
    started = time.perf_counter()
    if backend == "mlx":
        importlib.import_module("mlx_whisper")
        mx = importlib.import_module("mlx.core")
        if not mx.metal.is_available():
            raise PreparationError("此进程无法访问 Metal GPU；不能标为转写运行时可用。")
        with mx.stream(mx.gpu):
            value = mx.ones((1,)) + 1
            mx.eval(value)
        mx.synchronize()
        if value.item() != 2:
            raise PreparationError("Metal 执行检查失败。")
        execution = dict(device="metal", evaluated=True)
    else:
        for name in ("faster_whisper", "onnxruntime", "tokenizers", "numpy"):
            importlib.import_module(name)
        ct = importlib.import_module("ctranslate2")
        supported = sorted(ct.get_supported_compute_types("cpu"))
        if "int8" not in supported:
            raise PreparationError("CPU 运行时未报告 int8 支持。", dict(supported_compute_types=supported))
        execution = dict(device="cpu", compute_type="int8", supported_compute_types=supported,
                         real_model_inference=False)
    return dict(python=sys.executable, python_version=list(sys.version_info[:3]),
                isolated=sys.prefix != sys.base_prefix, backend=backend, versions=versions,
                lock_sha256=sha_file(spec["lock"]), execution=execution,
                runtime_import_seconds=time.perf_counter() - started, decoder=decoder_smoke(),
                real_audio_validated=False)


def prepare_model(backend, cache, protected=()):
    module = importlib.import_module("localize" if backend == "mlx" else "asr_backends")
    path, timing = module.model_directory(Path(cache), protected)
    return dict(model_path=str(absolute(path)), backend=backend, model=module.MODEL,
                revision=module.REVISION, **timing)


def validate_real_audio(path):
    path = absolute(path)
    if not path.is_file() or path.suffix.lower() not in (".mp3", ".wav"):
        raise PreparationError("--audio 必须指向实际存在的本地 MP3/WAV 文件。")
    return path


def check_audio(backend, cache, audio, force):
    from localize import decode, get_transcript
    source = validate_real_audio(audio)
    before = sha_file(source)
    started = time.perf_counter()
    pcm, decoder = decode(source)
    decode_seconds = time.perf_counter() - started
    transcript, timing = get_transcript(pcm, Path(cache), force=force, protected=[source], backend=backend)
    if before != sha_file(source):
        raise PreparationError("真实原音频在检查期间发生变化；本次结果不计通过。")
    segments = transcript["segments"]
    if not segments or not any(segment.get("words") for segment in segments):
        raise PreparationError("真实音频未返回可核对的词时码，不能标为转写可用。", dict(timing=timing))
    return dict(status="cache_reused" if timing["transcript_cache_hit"] else "transcribed",
                input=str(source), file_sha256=before, duration_seconds=len(pcm) / 32000,
                decode_seconds=decode_seconds, decoder=decoder, timing=timing,
                total_seconds=time.perf_counter() - started,
                real_audio_input=True, inference_executed=not timing["transcript_cache_hit"],
                segment_count=len(segments), word_count=sum(len(s.get("words", [])) for s in segments),
                listening_verified=False, production_adoption="not_evaluated")


def run_worker(args):
    # Keep downloads and compile caches in the selected local cache, not user defaults.
    cache = absolute(args.cache)
    os.environ["HF_HOME"] = str(cache / "hf-cache")
    os.environ["NUMBA_CACHE_DIR"] = str(cache / "numba-cache")
    try:
        if args._worker == "runtime":
            result = runtime_health(args._backend)
        elif args._worker == "model":
            result = prepare_model(args._backend, args.cache, [args.audio] if args.audio else [])
        else:
            result = check_audio(args._backend, args.cache, args.audio, args.force_transcribe)
        record = dict(ok=True, result=result)
    except Exception as error:
        details = getattr(error, "details", {})
        message = str(error)
        if platform.system() == "Windows" and any(term in message.lower() for term in ("dll load failed", "winerror 126", "vcruntime", "msvcp")):
            details = {**details, "system_action": "由 Codex 核对并安装微软官方 VC++ 2015–2022 x64 Runtime；如系统请求管理员授权，由用户正常授权后重跑。",
                       "official_source": "https://aka.ms/vs/17/release/vc_redist.x64.exe", "retryable": True}
        record = dict(ok=False, error=message, details=details)
    print(MARKER + json.dumps(record, ensure_ascii=False, allow_nan=False), flush=True)
    return 0 if record["ok"] else 1


def install_environment(state, spec, base_python, target, cache):
    """Only install into our unadopted pending venv, never repair one in place."""
    pending = state.data.get("pending_venv")
    if state.data.get("pending_target") != str(absolute(target)):
        pending = None
    pending_info = probe_python([str(venv_python(pending, spec))], spec) if pending else None
    # A valid unfinished install can resume missing packages. An invalid venv is preserved.
    if pending_info and pending_info["prefix"] != pending_info["base_prefix"] and not pending_info.get("system_site_packages"):
        directory = absolute(pending)
    else:
        directory = absolute(target)
        if directory.exists():
            directory = directory.with_name(directory.name + "-repair-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
        state.data["pending_venv"] = str(directory)
        state.data["pending_target"] = str(absolute(target))
        state.save()
        def create():
            completed = run_command([base_python, "-m", "venv", directory])
            if completed.returncode:
                raise PreparationError("独立 venv 创建失败；旧环境已保留。", dict(stderr=completed.stderr[-3000:], retryable=True))
            return dict(venv=str(directory), python=str(venv_python(directory, spec)))
        state.stage("create_environment", create)
    python = venv_python(directory, spec)
    def verify():
        info = probe_python([str(python)], spec)
        if not info or info["prefix"] == info["base_prefix"] or info.get("system_site_packages"):
            raise PreparationError("新建目标不是此平台的独立 CPython 3.12；未运行 pip。")
        return info
    state.stage("verify_new_python", verify)
    def install():
        completed = run_command([python, "-m", "pip", "install", "--cache-dir", cache / "pip-cache",
                                 "--only-binary=:all:", "-r", spec["lock"]])
        if completed.returncode:
            raise PreparationError("平台锁依赖安装未完成；同一 pending venv 可重跑恢复缺项。",
                                   dict(stderr=completed.stderr[-5000:], retryable=True, python=str(python)))
        return dict(python=str(python), lock=spec["lock"], lock_sha256=sha_file(spec["lock"]))
    state.stage("install_dependencies", install)
    return str(python)


def prepare(args):
    spec = platform_spec()
    root = absolute(args.state_root)
    cache = absolute(args.cache)
    audio = validate_real_audio(args.audio) if args.audio else None
    if audio:
        for output in (root / ".bootstrap.lock", root / "bootstrap-state.json"):
            if output.resolve() == audio.resolve() or (output.exists() and output.samefile(audio)):
                raise PreparationError("原音频与准备状态路径发生碰撞；保持原文件，改用另一状态目录。")
    if args.force_transcribe and not audio:
        raise PreparationError("--force-transcribe 仅与 --audio 一起使用。")
    with state_lock(root):
        state = State(root, spec)
        target = absolute(args.venv) if args.venv else root / "venv"
        candidates = [str(venv_python(target, spec))]
        if state.data.get("pending_target") == str(target) and state.data.get("pending_venv"):
            candidates.insert(0, str(venv_python(state.data["pending_venv"], spec)))
        if state.data.get("active_target") == str(target) and state.data.get("active_python"):
            candidates.insert(0, state.data["active_python"])
        if not args.venv:
            candidates = ([state.data.get("active_python"), args.python, sys.executable,
                           str(venv_python(REPOSITORY / ".codex_tmp/audio_v3/venv", spec))] + candidates)
        def inspect():
            failures = []
            for candidate in dict.fromkeys(path for path in candidates if path):
                info = probe_python([str(absolute(candidate))], spec)
                if not info or info["prefix"] == info["base_prefix"] or info.get("system_site_packages"):
                    continue
                try:
                    health = worker(info["executable"], "runtime", spec, cache)
                    return dict(python=info["executable"], health=health, failures=failures)
                except PreparationError as error:
                    failures.append(dict(python=info["executable"], error=str(error), details=error.details))
            return dict(python=None, health=None, failures=failures)
        inspected = state.stage("inspect_environment", inspect)
        python, runtime, failures = inspected["python"], inspected["health"], inspected["failures"]
        if python:
            state.stage("environment", lambda: dict(status="reused", python=python, health=runtime))
        else:
            system_problem = next((failure for failure in failures if failure["details"].get("system_action")), None)
            if system_problem:
                error = PreparationError(system_problem["error"], system_problem["details"])
                state.stage("environment", lambda: (_ for _ in ()).throw(error))
            if not args.install:
                error = (PreparationError("未找到健康的独立音频环境；Codex 应以 --install 继续准备。",
                          dict(environment_attempts=failures, codex_next_action="保持原目录，以 --install 重跑本命令。")))
                state.stage("environment", lambda: (_ for _ in ()).throw(error))
            base = next((info for command in python_commands(args.python)
                         if (info := probe_python(command, spec))), None)
            if not base:
                state.stage("python_runtime", lambda: (_ for _ in ()).throw(missing_python(spec)))
            state.stage("python_runtime", lambda: base)
            python = install_environment(state, spec, base["executable"], target, cache)
            runtime = state.stage("environment", lambda: worker(python, "runtime", spec, cache))
        state.data.update(active_python=python, active_venv=str(Path(python).parent.parent), active_target=str(target),
                          pending_venv=None, pending_target=None)
        state.save()
        if args.prepare_model:
            state.stage("fixed_model", lambda: worker(python, "model", spec, cache, audio))
        audio_result = state.stage("real_audio", lambda: worker(python, "audio", spec, cache, audio, args.force_transcribe)) if audio else None
        state.data.update(status="ready", current_stage=None,
                          last_check=dict(cache=str(cache), audio=audio_result or dict(status="not_requested", real_audio_validated=False),
                                          checked_at=utc_now()))
        state.save()
        return dict(ok=True, platform=spec, python=python, cache=str(cache),
                    state_file=str(state.path), environment="ready", decoder=runtime["decoder"],
                    model=state.data["stages"].get("fixed_model", {}).get("result") if args.prepare_model else dict(status="not_requested"),
                    audio=audio_result or dict(status="not_requested", real_audio_validated=False),
                    windows_validation="pending_real_machine" if spec["system"] != "Windows" else "this_machine_only")


def parser():
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    result.add_argument("--install", action="store_true", help="Codex 自动安装当前平台锁依赖到独立环境；健康环境直接复用")
    result.add_argument("--prepare-model", action="store_true", help="下载缺项并校验固定模型；已健康模型离线复用")
    result.add_argument("--audio", type=Path, help="真实本地 MP3/WAV；记录转写耗时或真实缓存命中，不代表制作采用")
    result.add_argument("--force-transcribe", action="store_true", help="仅配合 --audio 明确要求重新转写")
    result.add_argument("--python", type=Path, help="Codex 已定位的 CPython 3.12 绝对路径")
    result.add_argument("--venv", type=Path, help="优先检查的独立 venv；损坏时旁建，不覆盖")
    result.add_argument("--state-root", type=Path, default=REPOSITORY / ".codex_tmp/audio_bootstrap", help="可恢复阶段与新环境目录")
    result.add_argument("--cache", type=Path, default=REPOSITORY / ".codex_tmp/audio_v3", help="保留并复用的本地模型／词表缓存")
    result.add_argument("--_worker", choices=("runtime", "model", "audio"), help=argparse.SUPPRESS)
    result.add_argument("--_backend", choices=("mlx", "faster-whisper"), help=argparse.SUPPRESS)
    return result


def main(argv=None):
    # Console encodings vary under Windows; JSON files and child I/O stay UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parser().parse_args(argv)
    if args._worker:
        return run_worker(args)
    try:
        result = prepare(args)
    except KeyboardInterrupt:
        result = dict(ok=False, error="准备已中断；已完成阶段与 pending 环境保留，重跑可继续。", details=dict(retryable=True))
    except Exception as error:
        result = dict(ok=False, error=str(error), details=getattr(error, "details", {}))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
