#!/usr/bin/env python3
"""启用、暂停、恢复、关闭或查询 ChatGPT Pro 指挥工作流的持久状态。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


VALID_MODES = {"enabled", "paused", "disabled"}


def default_state_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return base / "state" / "chatgpt-pro-commander.json"


def load_state(path: Path) -> dict:
    if not path.exists():
        return {
            "schema_version": 1,
            "mode": "disabled",
            "enabled": False,
            "status": "disabled",
            "source": "default_missing",
            "updated_at": None,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": 1,
            "mode": "disabled",
            "enabled": False,
            "status": "disabled",
            "source": "invalid_fail_closed",
            "updated_at": None,
            "error": str(exc),
        }
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        return {
            "schema_version": 1,
            "mode": "disabled",
            "enabled": False,
            "status": "disabled",
            "source": "invalid_fail_closed",
            "updated_at": None,
            "error": "invalid schema",
        }
    stored_mode = payload.get("mode")
    if stored_mode not in VALID_MODES:
        legacy_enabled = payload.get("enabled")
        if isinstance(legacy_enabled, bool):
            stored_mode = "enabled" if legacy_enabled else "disabled"
        else:
            return {
                "schema_version": 1,
                "mode": "disabled",
                "enabled": False,
                "status": "disabled",
                "source": "invalid_fail_closed",
                "updated_at": None,
                "error": "invalid mode",
            }
    return {
        "schema_version": 1,
        "mode": stored_mode,
        "enabled": stored_mode == "enabled",
        "status": stored_mode,
        "source": "state_file",
        "updated_at": payload.get("updated_at"),
    }


def atomic_write(path: Path, mode: str) -> dict:
    if mode not in VALID_MODES:
        raise ValueError(f"无效模式: {mode}")
    payload = {
        "schema_version": 1,
        "mode": mode,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return load_state(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("enable", "pause", "resume", "disable", "status"))
    parser.add_argument("--state-file", help="覆盖默认状态路径，主要用于隔离测试")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()
    path = Path(args.state_file).expanduser() if args.state_file else default_state_path()
    if args.command == "enable":
        state = atomic_write(path, "enabled")
    elif args.command == "pause":
        state = atomic_write(path, "paused")
    elif args.command == "resume":
        state = atomic_write(path, "enabled")
    elif args.command == "disable":
        state = atomic_write(path, "disabled")
    else:
        state = load_state(path)
    state["state_file"] = str(path)
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        print(f"ChatGPT Pro 指挥工作流: {state['status']}")
        print(f"状态文件: {path}")
        if state["source"] == "invalid_fail_closed":
            print("状态文件无效，已按安全默认值停用。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
