#!/usr/bin/env python3
"""校验 ChatGPT Pro 的 PLAN/REVIEW 回复以及防重复消费 ledger。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import uuid
from pathlib import Path


REQUIRED_KEYS = {
    "protocol",
    "task_id",
    "response_id",
    "in_reply_to",
    "phase",
    "iteration",
    "verdict",
    "next_action",
    "reasoning_brief",
    "plan_or_findings",
    "acceptance_checks",
    "risks",
    "evidence_used",
}
JSON_FENCE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
MARKER_PATTERN = re.compile(r"^\[\[PRO_COMMANDER_REPLY_[0-9a-f]{32}\]\]$")


class ReplyError(ValueError):
    pass


def valid_uuid(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ReplyError(f"{field} 必须是 UUID 字符串")
    try:
        return str(uuid.UUID(value))
    except ValueError as exc:
        raise ReplyError(f"{field} 不是有效 UUID") from exc


def string_list(value: object, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ReplyError(f"{field} 必须是字符串数组")
    if nonempty and not value:
        raise ReplyError(f"{field} 不能为空")
    return value


def extract_payload(text: str, marker: str) -> dict:
    if not MARKER_PATTERN.fullmatch(marker):
        raise ReplyError("reply marker 格式无效")
    stripped = text.strip()
    if not stripped.startswith("PRO_COMMANDER/1 RESPONSE"):
        raise ReplyError("回复必须以 PRO_COMMANDER/1 RESPONSE 开头")
    if not stripped.splitlines() or stripped.splitlines()[-1].strip() != marker:
        raise ReplyError("reply marker 缺失或不是最后一行")
    matches = JSON_FENCE.findall(stripped)
    if len(matches) != 1:
        raise ReplyError("回复必须包含且只包含一个 JSON fenced block")
    try:
        payload = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise ReplyError(f"回复 JSON 无效: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReplyError("回复 JSON 必须是 object")
    return payload


def validate_payload(
    payload: dict,
    *,
    task_id: str,
    in_reply_to: str,
    phase: str,
    iteration: int,
) -> dict:
    missing = REQUIRED_KEYS - set(payload)
    extra = set(payload) - REQUIRED_KEYS
    if missing:
        raise ReplyError(f"缺少字段: {', '.join(sorted(missing))}")
    if extra:
        raise ReplyError(f"未知字段: {', '.join(sorted(extra))}")
    if payload["protocol"] != "PRO_COMMANDER/1":
        raise ReplyError("protocol 不匹配")
    if valid_uuid(payload["task_id"], "task_id") != str(uuid.UUID(task_id)):
        raise ReplyError("task_id 不匹配")
    response_id = valid_uuid(payload["response_id"], "response_id")
    if valid_uuid(payload["in_reply_to"], "in_reply_to") != str(uuid.UUID(in_reply_to)):
        raise ReplyError("in_reply_to 不匹配")
    expected_phase = phase.upper()
    if payload["phase"] != expected_phase or expected_phase not in {"PLAN", "REVIEW"}:
        raise ReplyError("phase 不匹配")
    if payload["iteration"] != iteration or not isinstance(payload["iteration"], int):
        raise ReplyError("iteration 不匹配")
    brief = payload["reasoning_brief"]
    if not isinstance(brief, str) or not brief.strip():
        raise ReplyError("reasoning_brief 不能为空")
    string_list(payload["plan_or_findings"], "plan_or_findings", nonempty=True)
    string_list(payload["acceptance_checks"], "acceptance_checks", nonempty=True)
    string_list(payload["risks"], "risks")
    string_list(payload["evidence_used"], "evidence_used")

    verdict = payload["verdict"]
    next_action = payload["next_action"]
    if expected_phase == "PLAN":
        if verdict != "NONE" or next_action != "EXECUTE":
            raise ReplyError("PLAN 必须使用 verdict NONE 和 next_action EXECUTE")
    else:
        expected = {"PASS": "COMPLETE", "REVISE": "REPAIR", "BLOCKED": "STOP"}
        if verdict not in expected or next_action != expected[verdict]:
            raise ReplyError("REVIEW 的 verdict 与 next_action 不一致")
        if iteration >= 2 and verdict == "REVISE":
            raise ReplyError("第二次执行后不得继续自动 REVISE")
    return {
        "task_id": str(uuid.UUID(task_id)),
        "response_id": response_id,
        "in_reply_to": str(uuid.UUID(in_reply_to)),
        "phase": expected_phase,
        "iteration": iteration,
        "verdict": verdict,
        "next_action": next_action,
    }


def load_ledger(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 1, "responses": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ReplyError("ledger schema 无效")
    responses = payload.get("responses")
    if not isinstance(responses, list):
        raise ReplyError("ledger responses 无效")
    return payload


def atomic_write_json(path: Path, payload: dict) -> None:
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


def record_response(ledger_path: Path, record: dict) -> None:
    ledger = load_ledger(ledger_path)
    for existing in ledger["responses"]:
        if existing.get("task_id") != record["task_id"]:
            continue
        if existing.get("response_id") == record["response_id"]:
            raise ReplyError("response_id 已经消费")
        if existing.get("in_reply_to") == record["in_reply_to"]:
            raise ReplyError("该请求已经消费过一个回复")
    ledger["responses"].append(record)
    atomic_write_json(ledger_path, ledger)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reply_file")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--in-reply-to", required=True)
    parser.add_argument("--phase", required=True, choices=("PLAN", "REVIEW"))
    parser.add_argument("--iteration", required=True, type=int, choices=(1, 2))
    parser.add_argument("--marker", required=True)
    parser.add_argument("--ledger", help="校验成功后原子记录 response_id；省略时只读校验")
    args = parser.parse_args()

    try:
        task_id = valid_uuid(args.task_id, "expected task_id")
        message_id = valid_uuid(args.in_reply_to, "expected in_reply_to")
        text = Path(args.reply_file).read_text(encoding="utf-8")
        payload = extract_payload(text, args.marker)
        record = validate_payload(
            payload,
            task_id=task_id,
            in_reply_to=message_id,
            phase=args.phase,
            iteration=args.iteration,
        )
        if args.ledger:
            record_response(Path(args.ledger), record)
    except (OSError, json.JSONDecodeError, ReplyError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps({"ok": True, **record}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
