#!/usr/bin/env python3
"""为 ChatGPT Pro 指挥流程生成经过扫描的源码 ZIP、Markdown Bundle 和清单。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = 1
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "bower_components",
    "coverage",
    "dist",
    "build",
    "target",
    "deriveddata",
    "browser-profile",
    "chrome-profile",
    "user-data-dir",
    "browser_state",
    ".browser",
    ".auth",
    "session-storage",
    "local-storage",
}
BLOCKED_NAMES = {
    ".npmrc",
    ".pypirc",
    ".netrc",
    "auth.json",
    "cookies",
    "cookies.json",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "credentials.json",
    "login data",
    "local state",
    "secrets.json",
    "storage-state.json",
    "storagestate.json",
    "web data",
}
BLOCKED_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".db",
}
SKIP_FILES = {".DS_Store"}

HIGH_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("gitlab_token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    (
        "authorization_header",
        re.compile(r"(?i)\bAuthorization\s*:\s*(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{12,}"),
    ),
    ("cookie_header", re.compile(r"(?i)\bCookie\s*:\s*[^\n]{20,}")),
    ("personal_absolute_path", re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/[^/\s]+/")),
    ("windows_user_path", re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+\\")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(?:password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?"
            r"(?!<|\$\{|REDACTED|CHANGEME|EXAMPLE)[^\s'\"]{12,}"
        ),
    ),
)

WARN_PATTERNS = (
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone_cn", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("id_card_cn", re.compile(r"\b\d{17}[\dXx]\b")),
    ("private_network_url", re.compile(r"https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)[^\s]*")),
)

LANGUAGE_BY_SUFFIX = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".css": "css",
    ".go": "go",
    ".h": "c",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "jsx",
    ".md": "markdown",
    ".mjs": "javascript",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "bash",
    ".sql": "sql",
    ".swift": "swift",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


class PacketError(RuntimeError):
    """输入范围或安全检查不允许生成附件。"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if not resolved.is_dir():
        raise PacketError(f"项目根目录不存在或不是目录: {resolved}")
    home = Path.home().resolve()
    broad = {Path("/"), home, home / "Documents", home / "Downloads", home / "Desktop"}
    if resolved in broad:
        raise PacketError("拒绝打包过宽目录；请选择一个明确的项目根目录。")
    return resolved


def exclusion_reason(path: Path, root: Path) -> str | None:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return "outside_root"
    if path.is_symlink():
        return "symlink"
    lowered_parts = {part.lower() for part in relative.parts[:-1]}
    if lowered_parts & SKIP_DIRS:
        return "excluded_directory"
    name_lower = path.name.lower()
    if path.name in SKIP_FILES:
        return "excluded_file"
    if name_lower == ".env" or name_lower.startswith(".env."):
        return "credential_filename"
    if name_lower in BLOCKED_NAMES or path.suffix.lower() in BLOCKED_SUFFIXES:
        return "credential_or_runtime_filename"
    return None


def run_git(root: Path, args: list[str], *, check: bool = False) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=False,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        if check:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise PacketError(f"Git 命令失败: {detail}")
        return None
    return result.stdout.decode("utf-8", errors="replace")


def git_metadata(root: Path) -> tuple[dict, Path | None, str]:
    top_raw = run_git(root, ["rev-parse", "--show-toplevel"])
    if not top_raw:
        return (
            {
                "is_git_repository": False,
                "branch": None,
                "commit": None,
                "dirty": None,
                "status": ["not-a-git-repository"],
            },
            None,
            ".",
        )
    top = Path(top_raw.strip()).resolve()
    if not is_within(root, top):
        raise PacketError("项目根目录与 Git 根目录关系异常。")
    scope = "." if root == top else root.relative_to(top).as_posix()
    branch = (run_git(top, ["branch", "--show-current"]) or "").strip() or None
    commit = (run_git(top, ["rev-parse", "HEAD"]) or "").strip() or None
    status_raw = run_git(top, ["status", "--short", "--branch", "--untracked-files=all", "--", scope]) or ""
    status = [line for line in status_raw.splitlines() if line]
    dirty = any(not line.startswith("##") for line in status)
    return (
        {
            "is_git_repository": True,
            "branch": branch,
            "commit": commit,
            "dirty": dirty,
            "status": status,
        },
        top,
        scope,
    )


def iter_directory(directory: Path) -> Iterable[Path]:
    for item in sorted(directory.rglob("*"), key=lambda value: value.as_posix()):
        if item.is_file() or item.is_symlink():
            yield item


def git_candidates(root: Path, git_top: Path, scope: str) -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(git_top),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            scope,
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise PacketError(f"无法列出 Git 文件: {detail}")
    paths: list[Path] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        candidate = git_top / raw.decode("utf-8", errors="surrogateescape")
        if is_within(candidate.resolve(strict=False), root):
            paths.append(candidate)
    return paths


def explicit_candidates(root: Path, includes: list[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in includes:
        requested = Path(raw).expanduser()
        candidate = requested if requested.is_absolute() else root / requested
        lexical = candidate.absolute()
        if not is_within(lexical, root):
            raise PacketError(f"include 超出项目根目录: {raw}")
        if candidate.is_symlink():
            paths.append(candidate)
            continue
        resolved = candidate.resolve(strict=False)
        if not is_within(resolved, root):
            raise PacketError(f"include 解析后超出项目根目录: {raw}")
        if candidate.is_file():
            paths.append(candidate)
        elif candidate.is_dir():
            paths.extend(iter_directory(candidate))
        else:
            raise PacketError(f"include 不存在: {raw}")
    return paths


def line_number(text: str, start: int) -> int:
    return text.count("\n", 0, start) + 1


def scan_text(text: str, label: str) -> list[dict]:
    findings: list[dict] = []
    for severity, patterns in (("high", HIGH_PATTERNS), ("warning", WARN_PATTERNS)):
        for kind, pattern in patterns:
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "severity": severity,
                        "type": kind,
                        "path": label,
                        "line": line_number(text, match.start()),
                    }
                )
    return findings


def try_text(data: bytes) -> str | None:
    if b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def markdown_fence(text: str) -> str:
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def safe_write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    path.chmod(0o600)


def safe_write_json(path: Path, payload: dict) -> None:
    safe_write_bytes(path, (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def zip_write(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_packet(args: argparse.Namespace) -> dict:
    root = validate_root(Path(args.root))
    task_file = Path(args.task_file).expanduser().resolve()
    if not task_file.is_file() or task_file.is_symlink():
        raise PacketError("TASK 文件不存在、不是普通文件或是符号链接。")
    task_data = task_file.read_bytes()
    task_text = try_text(task_data)
    if task_text is None:
        raise PacketError("TASK 文件必须是 UTF-8 文本。")

    output_dir = Path(args.output_dir).expanduser().resolve(strict=False)
    if is_within(output_dir, root):
        raise PacketError("输出目录必须位于项目根目录之外。")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir.chmod(0o700)

    git, git_top, scope = git_metadata(root)
    if args.include:
        raw_candidates = explicit_candidates(root, args.include)
        selection_mode = "explicit"
    elif git_top is not None:
        raw_candidates = git_candidates(root, git_top, scope)
        selection_mode = "git-tracked-and-unignored-untracked"
    else:
        raw_candidates = list(iter_directory(root))
        selection_mode = "recursive-non-git"

    candidates: dict[str, Path] = {}
    skipped: list[dict] = []
    for path in raw_candidates:
        lexical = path.absolute()
        try:
            label = lexical.relative_to(root).as_posix()
        except ValueError:
            skipped.append({"path": path.name, "reason": "outside_root"})
            continue
        reason = exclusion_reason(lexical, root)
        if reason:
            skipped.append({"path": label, "reason": reason})
            continue
        resolved = lexical.resolve(strict=False)
        if not is_within(resolved, root):
            skipped.append({"path": label, "reason": "resolved_outside_root"})
            continue
        if not resolved.is_file():
            skipped.append({"path": label, "reason": "not_regular_file"})
            continue
        if resolved == task_file:
            continue
        candidates[label] = resolved

    selected: list[dict] = []
    contents: dict[str, bytes] = {}
    findings = scan_text(task_text, "TASK.md")
    total = 0
    for label in sorted(candidates):
        path = candidates[label]
        size = path.stat().st_size
        if size > args.max_file_bytes:
            skipped.append({"path": label, "reason": "max_file_bytes", "size": size})
            continue
        if total + size > args.max_total_bytes:
            skipped.append({"path": label, "reason": "max_total_bytes", "size": size})
            continue
        data = path.read_bytes()
        text = try_text(data)
        if text is None:
            skipped.append({"path": label, "reason": "unverified_binary", "size": len(data)})
            continue
        file_findings = scan_text(data.decode("utf-8", errors="ignore"), label)
        findings.extend(file_findings)
        record = {
            "path": label,
            "size": len(data),
            "sha256": sha256_bytes(data),
            "content_type": "text",
            "warning_count": sum(1 for item in file_findings if item["severity"] == "warning"),
        }
        selected.append(record)
        contents[label] = data
        total += len(data)

    high_count = sum(1 for item in findings if item["severity"] == "high")
    warning_count = sum(1 for item in findings if item["severity"] == "warning")
    safety = {
        "schema_version": SCHEMA_VERSION,
        "task_id": args.task_id,
        "ok": high_count == 0 and not (args.fail_on_warnings and warning_count > 0),
        "high_count": high_count,
        "warning_count": warning_count,
        "findings": findings,
        "note": "报告不包含匹配到的敏感值，只记录类型、相对路径和行号。",
    }
    safety_path = output_dir / f"{args.task_id}-safety.json"
    safe_write_json(safety_path, safety)
    if not safety["ok"]:
        raise PacketError(f"安全扫描未通过；详情见 {safety_path.name}")

    manifest_base = {
        "schema_version": SCHEMA_VERSION,
        "task_id": args.task_id,
        "created_at": now_iso(),
        "workspace": root.name,
        "git": git,
        "selection": {
            "mode": selection_mode,
            "file_count": len(selected),
            "total_bytes": total,
            "max_file_bytes": args.max_file_bytes,
            "max_total_bytes": args.max_total_bytes,
        },
        "task": {"size": len(task_data), "sha256": sha256_bytes(task_data)},
        "files": selected,
        "skipped": sorted(skipped, key=lambda item: (item.get("path", ""), item.get("reason", ""))),
        "safety": {
            "ok": True,
            "high_count": high_count,
            "warning_count": warning_count,
            "report": safety_path.name,
        },
    }

    archive_path = output_dir / f"{args.task_id}-source.zip"
    internal_manifest = json.dumps(manifest_base, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    with zipfile.ZipFile(archive_path, "w") as archive:
        zip_write(archive, "TASK.md", task_data)
        zip_write(archive, "MANIFEST.json", internal_manifest)
        for label in sorted(contents):
            zip_write(archive, f"source/{label}", contents[label])
    archive_path.chmod(0o600)

    bundle_lines = [
        "# ChatGPT Pro 指挥任务附件包",
        "",
        f"- Task ID: `{args.task_id}`",
        f"- Workspace: `{root.name}`",
        f"- Files: {len(selected)}",
        "",
        "## TASK",
        "",
        task_text.rstrip(),
        "",
        "## Source files",
    ]
    for record in selected:
        if record["content_type"] != "text":
            continue
        label = record["path"]
        text = contents[label].decode("utf-8")
        fence = markdown_fence(text)
        language = LANGUAGE_BY_SUFFIX.get(Path(label).suffix.lower(), "text")
        safe_label = label.replace("`", "_")
        bundle_lines.extend(
            [
                "",
                f"### `{safe_label}`",
                "",
                f"{fence}{language}",
                text.rstrip(),
                fence,
            ]
        )
    bundle_path = output_dir / f"{args.task_id}-bundle.md"
    safe_write_bytes(bundle_path, ("\n".join(bundle_lines).rstrip() + "\n").encode("utf-8"))

    manifest = dict(manifest_base)
    manifest["artifacts"] = {
        "source_zip": {
            "name": archive_path.name,
            "size": archive_path.stat().st_size,
            "sha256": sha256_file(archive_path),
        },
        "markdown_bundle": {
            "name": bundle_path.name,
            "size": bundle_path.stat().st_size,
            "sha256": sha256_file(bundle_path),
        },
        "safety_report": {
            "name": safety_path.name,
            "size": safety_path.stat().st_size,
            "sha256": sha256_file(safety_path),
        },
    }
    manifest_path = output_dir / f"{args.task_id}-manifest.json"
    safe_write_json(manifest_path, manifest)

    return {
        "ok": True,
        "task_id": args.task_id,
        "manifest": str(manifest_path),
        "source_zip": str(archive_path),
        "markdown_bundle": str(bundle_path),
        "safety_report": str(safety_path),
        "source_zip_sha256": manifest["artifacts"]["source_zip"]["sha256"],
        "file_count": len(selected),
        "warning_count": warning_count,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="明确的项目根目录")
    parser.add_argument("--task-file", required=True, help="UTF-8 TASK.md 路径")
    parser.add_argument("--task-id", required=True, help="当前任务 UUID")
    parser.add_argument("--output-dir", required=True, help="项目外的证据输出目录")
    parser.add_argument("--include", action="append", default=[], help="相对项目根目录的文件或目录，可重复")
    parser.add_argument("--max-file-bytes", type=int, default=1_000_000)
    parser.add_argument("--max-total-bytes", type=int, default=20_000_000)
    parser.add_argument("--fail-on-warnings", action="store_true", help="把普通敏感信息 warning 也作为阻断项")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = build_packet(args)
    except (PacketError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
