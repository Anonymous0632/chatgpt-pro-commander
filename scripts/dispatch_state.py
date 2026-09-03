#!/usr/bin/env python3
"""持久记录一次浏览器消息的 NOT_SENT/SENT/UNKNOWN 防重状态。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


class DispatchError(ValueError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path: Path, payload: dict) -> None:
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


def load_state(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "task_id", "message_id", "state", "send_attempts", "conversation_url", "created_at", "updated_at"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise DispatchError("发送状态文件字段无效")
    if payload["schema_version"] != 1 or payload["state"] not in {"NOT_SENT", "SENT", "UNKNOWN"}:
        raise DispatchError("发送状态文件 schema 或 state 无效")
    uuid.UUID(payload["task_id"])
    uuid.UUID(payload["message_id"])
    if not isinstance(payload["send_attempts"], int) or payload["send_attempts"] not in {0, 1}:
        raise DispatchError("send_attempts 无效")
    return payload


def validate_chatgpt_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc.lower() not in {"chatgpt.com", "www.chatgpt.com"}:
        raise DispatchError("conversation URL 必须是 chatgpt.com 的 HTTPS 地址")
    return value


def execute(path: Path, command: str, task_id: str | None, message_id: str | None, url: str | None) -> dict:
    if command == "init":
        if path.exists():
            raise DispatchError("状态文件已存在；不得覆盖或重置")
        if not task_id or not message_id:
            raise DispatchError("init 需要 task_id 和 message_id")
        canonical_task = str(uuid.UUID(task_id))
        canonical_message = str(uuid.UUID(message_id))
        timestamp = now_iso()
        payload = {
            "schema_version": 1,
            "task_id": canonical_task,
            "message_id": canonical_message,
            "state": "NOT_SENT",
            "send_attempts": 0,
            "conversation_url": None,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        atomic_write(path, payload)
        return payload

    payload = load_state(path)
    if task_id and str(uuid.UUID(task_id)) != payload["task_id"]:
        raise DispatchError("task_id 与状态文件不匹配")
    if message_id and str(uuid.UUID(message_id)) != payload["message_id"]:
        raise DispatchError("message_id 与状态文件不匹配")

    if command == "status":
        return payload
    if command == "can-send":
        return {**payload, "can_send": payload["state"] == "NOT_SENT" and payload["send_attempts"] == 0}
    if command == "set-conversation":
        if not url:
            raise DispatchError("set-conversation 需要 --url")
        payload["conversation_url"] = validate_chatgpt_url(url)
    elif command == "arm":
        if payload["state"] != "NOT_SENT" or payload["send_attempts"] != 0:
            raise DispatchError("只有从未尝试发送的 NOT_SENT 消息可以 arm")
        payload["state"] = "UNKNOWN"
        payload["send_attempts"] = 1
    elif command == "mark-sent":
        if payload["state"] != "UNKNOWN" or payload["send_attempts"] != 1:
            raise DispatchError("只有已 arm 的 UNKNOWN 消息可以标记为 SENT")
        payload["state"] = "SENT"
    else:
        raise DispatchError(f"未知命令: {command}")
    payload["updated_at"] = now_iso()
    atomic_write(path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_file")
    parser.add_argument("command", choices=("init", "status", "can-send", "set-conversation", "arm", "mark-sent"))
    parser.add_argument("--task-id")
    parser.add_argument("--message-id")
    parser.add_argument("--url")
    args = parser.parse_args()
    try:
        payload = execute(Path(args.state_file), args.command, args.task_id, args.message_id, args.url)
    except (OSError, json.JSONDecodeError, DispatchError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **payload}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

