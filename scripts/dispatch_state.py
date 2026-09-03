#!/usr/bin/env python3
"""Persist NOT_SENT/SENT/UNKNOWN duplicate-safe browser message state."""

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
        raise DispatchError("Invalid dispatch-state fields")
    if payload["schema_version"] != 1 or payload["state"] not in {"NOT_SENT", "SENT", "UNKNOWN"}:
        raise DispatchError("Invalid dispatch-state schema or state")
    uuid.UUID(payload["task_id"])
    uuid.UUID(payload["message_id"])
    if not isinstance(payload["send_attempts"], int) or payload["send_attempts"] not in {0, 1}:
        raise DispatchError("Invalid send_attempts")
    return payload


def validate_chatgpt_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc.lower() not in {"chatgpt.com", "www.chatgpt.com"}:
        raise DispatchError("Conversation URL must be an HTTPS chatgpt.com URL")
    return value


def execute(path: Path, command: str, task_id: str | None, message_id: str | None, url: str | None) -> dict:
    if command == "init":
        if path.exists():
            raise DispatchError("State file already exists and cannot be overwritten or reset")
        if not task_id or not message_id:
            raise DispatchError("init requires task_id and message_id")
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
        raise DispatchError("task_id does not match the state file")
    if message_id and str(uuid.UUID(message_id)) != payload["message_id"]:
        raise DispatchError("message_id does not match the state file")

    if command == "status":
        return payload
    if command == "can-send":
        return {**payload, "can_send": payload["state"] == "NOT_SENT" and payload["send_attempts"] == 0}
    if command == "set-conversation":
        if not url:
            raise DispatchError("set-conversation requires --url")
        payload["conversation_url"] = validate_chatgpt_url(url)
    elif command == "arm":
        if payload["state"] != "NOT_SENT" or payload["send_attempts"] != 0:
            raise DispatchError("Only an unattempted NOT_SENT message can be armed")
        payload["state"] = "UNKNOWN"
        payload["send_attempts"] = 1
    elif command == "mark-sent":
        if payload["state"] != "UNKNOWN" or payload["send_attempts"] != 1:
            raise DispatchError("Only an armed UNKNOWN message can be marked SENT")
        payload["state"] = "SENT"
    else:
        raise DispatchError(f"Unknown command: {command}")
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
