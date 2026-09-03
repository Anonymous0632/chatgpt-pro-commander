#!/usr/bin/env python3
"""校验发送前保存的 Chat/Pro 浏览器门禁记录。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


REQUIRED_KEYS = {
    "schema_version",
    "surface",
    "chat_selected",
    "work_active",
    "active_model_label",
    "pro_control_selected",
    "evidence_scope",
    "inspection_method",
    "selection_path",
    "observed_at",
}
PRO_TOKEN = re.compile(r"(?<![A-Za-z0-9])Pro(?![A-Za-z0-9])", re.IGNORECASE)


def validate_gate(payload: dict) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_KEYS - set(payload)
    extra = set(payload) - REQUIRED_KEYS
    if missing:
        errors.append(f"缺少字段: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"未知字段: {', '.join(sorted(extra))}")
    if payload.get("schema_version") != 1:
        errors.append("schema_version 必须为 1")
    if payload.get("surface") not in {"iab", "chrome"}:
        errors.append("surface 必须为 iab 或 chrome")
    if payload.get("chat_selected") is not True:
        errors.append("Chat/聊天未确认选中")
    if payload.get("work_active") is not False:
        errors.append("Work/工作必须处于未激活状态")
    label = payload.get("active_model_label")
    if not isinstance(label, str) or not PRO_TOKEN.search(label):
        errors.append("活动模型标签不包含独立的 Pro 词元")
    if isinstance(label, str) and re.search(r"\bWork\b|工作", label, re.IGNORECASE):
        errors.append("活动模型标签不能来自 Work/工作")
    if payload.get("pro_control_selected") is not True:
        errors.append("没有证明 Pro 选项处于选中状态")
    if payload.get("evidence_scope") != "active_model_control":
        errors.append("证据必须来自活动模型控件")
    if payload.get("inspection_method") not in {"dom", "ax"}:
        errors.append("inspection_method 必须为 dom 或 ax")
    if payload.get("selection_path") not in {"already_pro", "direct_option"}:
        errors.append("selection_path 无效")
    observed = payload.get("observed_at")
    if not isinstance(observed, str):
        errors.append("observed_at 必须是 ISO-8601 字符串")
    else:
        try:
            parsed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                errors.append("observed_at 必须包含时区")
        except ValueError:
            errors.append("observed_at 不是有效 ISO-8601 时间")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate_json")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.gate_json).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("门禁记录必须是 JSON object")
        errors = validate_gate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors = [str(exc)]
    result = {"ok": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

