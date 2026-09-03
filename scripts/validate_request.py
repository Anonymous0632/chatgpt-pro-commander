#!/usr/bin/env python3
"""Validate PLAN/REVIEW protocol, IDs, and reply marker before sending."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path


REQUIRED_KEYS = {
    "protocol",
    "task_id",
    "message_id",
    "phase",
    "iteration",
    "reply_marker",
    "workspace",
    "objective",
    "acceptance_criteria",
    "authorized_actions",
    "forbidden_actions",
    "known_facts",
    "unknowns",
}
JSON_FENCE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
MARKER_PATTERN = re.compile(r"^\[\[PRO_COMMANDER_REPLY_[0-9a-f]{32}\]\]$")


class RequestError(ValueError):
    pass


def valid_uuid(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise RequestError(f"{field} must be a UUID string")
    try:
        return str(uuid.UUID(value))
    except ValueError as exc:
        raise RequestError(f"{field} is not a valid UUID") from exc


def string_list(value: object, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RequestError(f"{field} must be an array of strings")
    if nonempty and not value:
        raise RequestError(f"{field} cannot be empty")
    return value


def extract_payload(text: str) -> dict:
    stripped = text.strip()
    if not stripped.startswith("PRO_COMMANDER/1 REQUEST"):
        raise RequestError("Request must start with PRO_COMMANDER/1 REQUEST")
    matches = JSON_FENCE.findall(stripped)
    if len(matches) != 1:
        raise RequestError("Request must contain exactly one fenced JSON block")
    try:
        payload = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise RequestError(f"Invalid request JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RequestError("Request JSON must be an object")
    return payload


def validate_payload(
    payload: dict,
    *,
    task_id: str,
    message_id: str,
    phase: str,
    iteration: int,
) -> dict:
    missing = REQUIRED_KEYS - set(payload)
    extra = set(payload) - REQUIRED_KEYS
    if missing:
        raise RequestError(f"Missing fields: {', '.join(sorted(missing))}")
    if extra:
        raise RequestError(f"Unknown fields: {', '.join(sorted(extra))}")
    if payload["protocol"] != "PRO_COMMANDER/1":
        raise RequestError("protocol mismatch")
    canonical_task = valid_uuid(payload["task_id"], "task_id")
    canonical_message = valid_uuid(payload["message_id"], "message_id")
    if canonical_task != str(uuid.UUID(task_id)):
        raise RequestError("task_id mismatch")
    if canonical_message != str(uuid.UUID(message_id)):
        raise RequestError("message_id mismatch")
    expected_phase = phase.upper()
    if expected_phase not in {"PLAN", "REVIEW"} or payload["phase"] != expected_phase:
        raise RequestError("phase mismatch")
    if not isinstance(payload["iteration"], int) or payload["iteration"] != iteration:
        raise RequestError("iteration mismatch")
    if expected_phase == "PLAN" and iteration != 1:
        raise RequestError("PLAN iteration must be 1")
    marker = payload["reply_marker"]
    if not isinstance(marker, str) or not MARKER_PATTERN.fullmatch(marker):
        raise RequestError("Invalid reply_marker format")
    workspace = payload["workspace"]
    if not isinstance(workspace, str) or not workspace.strip() or "/" in workspace or "\\" in workspace:
        raise RequestError("workspace must be only the project directory name")
    objective = payload["objective"]
    if not isinstance(objective, str) or not objective.strip():
        raise RequestError("objective cannot be empty")
    string_list(payload["acceptance_criteria"], "acceptance_criteria", nonempty=True)
    string_list(payload["authorized_actions"], "authorized_actions")
    string_list(payload["forbidden_actions"], "forbidden_actions", nonempty=True)
    string_list(payload["known_facts"], "known_facts")
    string_list(payload["unknowns"], "unknowns")
    return {
        "task_id": canonical_task,
        "message_id": canonical_message,
        "phase": expected_phase,
        "iteration": iteration,
        "reply_marker": marker,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_file")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--message-id", required=True)
    parser.add_argument("--phase", required=True, choices=("PLAN", "REVIEW"))
    parser.add_argument("--iteration", required=True, type=int, choices=(1, 2))
    args = parser.parse_args()
    try:
        task_id = valid_uuid(args.task_id, "expected task_id")
        message_id = valid_uuid(args.message_id, "expected message_id")
        text = Path(args.request_file).read_text(encoding="utf-8")
        payload = extract_payload(text)
        record = validate_payload(
            payload,
            task_id=task_id,
            message_id=message_id,
            phase=args.phase,
            iteration=args.iteration,
        )
    except (OSError, json.JSONDecodeError, RequestError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **record}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
