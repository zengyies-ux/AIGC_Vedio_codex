#!/usr/bin/env python3
"""Build the clean Seedance Codex core package from an explicit whitelist.

This script is intentionally manual. Run it only after the user explicitly asks
for a new package release.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGING_DIR = REPO_ROOT / "packaging"
RELEASES_DIR = REPO_ROOT / "releases"

CORE_FILES = [
    "AGENTS.md",
    "ROADMAP.md",
    "memories/seedance_workflow/README.md",
    "memories/seedance_workflow/director_os.md",
    "memories/seedance_workflow/model_behavior.md",
    "memories/seedance_workflow/seedance_2_5_technical_notes.md",
    "memories/seedance_workflow/execution_rules.md",
    "memories/seedance_workflow/prompt_template.md",
    "memories/seedance_workflow/continuity_and_review.md",
    "memories/seedance_workflow/director_patterns.md",
    "memories/seedance_workflow/animal_city_motion.md",
    "memories/seedance_workflow/visual_language_learning_notes.md",
    "memories/seedance_workflow/live_action_dialogue_drama.md",
    "memories/seedance_workflow/field_lessons.md",
    "memories/seedance_workflow/projects/PROJECT_TEMPLATE.md",
]

ABSOLUTE_PATH_RE = re.compile(r"/(?:Users|var/folders)/")
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
CONFLICT_RE = re.compile(r"^(?:<<<<<<<|=======|>>>>>>>)", re.MULTILINE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_text(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def write_clean_project_index(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """# 项目索引

本核心学习包不包含任何历史或活动项目。开始新项目时，先使用[PROJECT_TEMPLATE.md](./PROJECT_TEMPLATE.md)建立独立目录，再把当前项目的概览、制作状态、素材索引与提示词索引登记在本页。

不要从其他工作区猜测或自动导入旧项目；只有用户明确提供或要求继续的项目，才进入当前上下文。
""",
        encoding="utf-8",
    )


def package_info(config: dict[str, str]) -> str:
    return f"""# 核心包信息

- 包名：`{config['package_name']}`
- 版本：`{config['version']}`
- 发布日期：`{config['release_date']}`
- 更新策略：仅在用户明确要求时手动更新
- 内容：现行Seedance提示词规则、模板、技术摘要、匿名经验与空白项目结构
- 排除：所有历史项目、项目纪念目录、资产、审片、旧提示词、旧2.0 Skill与团队SOP

## 本版摘要

{config['summary']}

## 开始使用

先读`AGENTS.md`。`README.md`说明包结构，`ROADMAP.md`只记录未来方向，不是当前强制规则。文件级校验值见`MANIFEST.sha256`。
"""


def validate_package(package_root: Path) -> dict[str, int]:
    files = sorted(path for path in package_root.rglob("*") if path.is_file())
    markdown_files = [path for path in files if path.suffix.lower() == ".md"]
    errors: list[str] = []

    forbidden_names = {"PROJECT_HISTORY.md", ".DS_Store"}
    forbidden_parts = {"Skill", "团队专项SOP", "assets", "reviews", "prompts", "source", "tmp", "__MACOSX"}
    for path in files:
        relative = path.relative_to(package_root)
        if path.name in forbidden_names or any(part in forbidden_parts for part in relative.parts):
            errors.append(f"forbidden file: {relative}")

    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(package_root)
        if ABSOLUTE_PATH_RE.search(text):
            errors.append(f"absolute local path: {relative}")
        if text.count("```") % 2:
            errors.append(f"unbalanced code fence: {relative}")
        if CONFLICT_RE.search(text):
            errors.append(f"merge conflict marker: {relative}")

        for match in LINK_RE.finditer(text):
            raw = match.group(1).strip()
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            raw = raw.split("#", 1)[0]
            if not raw or SCHEME_RE.match(raw) or raw.startswith("/"):
                continue
            if not (path.parent / raw).resolve().exists():
                errors.append(f"missing link from {relative}: {raw}")

    if errors:
        raise RuntimeError("Package validation failed:\n" + "\n".join(errors))

    return {
        "file_count": len(files),
        "markdown_count": len(markdown_files),
        "uncompressed_bytes": sum(path.stat().st_size for path in files),
    }


def write_manifest(package_root: Path) -> None:
    entries = []
    for path in sorted(p for p in package_root.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256"):
        relative = path.relative_to(package_root).as_posix()
        entries.append(f"{sha256_file(path)}  {relative}")
    (package_root / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def write_deterministic_zip(package_root: Path, archive_path: Path, release_date: str) -> None:
    date = datetime.strptime(release_date, "%Y-%m-%d")
    timestamp = (date.year, date.month, date.day, 0, 0, 0)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.unlink(missing_ok=True)

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in package_root.rglob("*") if p.is_file()):
            relative = Path(package_root.name) / path.relative_to(package_root)
            info = zipfile.ZipInfo(relative.as_posix(), timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    config = json.loads((PACKAGING_DIR / "package_config.json").read_text(encoding="utf-8"))
    folder_name = f"{config['package_name']}_v{config['version']}"
    archive_name = f"{folder_name}_{config['release_date']}.zip"
    archive_path = RELEASES_DIR / archive_name

    with tempfile.TemporaryDirectory(prefix="seedance_core_package_") as temp_dir:
        package_root = Path(temp_dir) / folder_name
        package_root.mkdir(parents=True)

        copy_text(PACKAGING_DIR / "CORE_PACKAGE_README.md", package_root / "README.md")
        copy_text(PACKAGING_DIR / "CHANGELOG.md", package_root / "CHANGELOG.md")
        for relative in CORE_FILES:
            source = REPO_ROOT / relative
            if not source.exists():
                raise FileNotFoundError(f"Missing whitelisted source file: {relative}")
            copy_text(source, package_root / relative)

        write_clean_project_index(package_root / "memories/seedance_workflow/projects/INDEX.md")
        (package_root / "PACKAGE_INFO.md").write_text(package_info(config), encoding="utf-8")
        write_manifest(package_root)
        stats = validate_package(package_root)
        write_deterministic_zip(package_root, archive_path, config["release_date"])

    archive_sha = sha256_file(archive_path)
    sha_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    sha_path.write_text(f"{archive_sha}  {archive_path.name}\n", encoding="utf-8")

    metadata = {
        "package_name": config["package_name"],
        "version": config["version"],
        "release_date": config["release_date"],
        "update_policy": config["update_policy"],
        "archive": archive_path.name,
        "sha256": archive_sha,
        **stats,
    }
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    (RELEASES_DIR / "latest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
