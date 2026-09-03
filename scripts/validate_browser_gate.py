#!/usr/bin/env python3
"""Validate the saved Chat/Pro browser gate before sending."""

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
        errors.append(f"Missing fields: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Unknown fields: {', '.join(sorted(extra))}")
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("surface") not in {"iab", "chrome"}:
        errors.append("surface must be iab or chrome")
    if payload.get("chat_selected") is not True:
        errors.append("Chat is not confirmed as selected")
    if payload.get("work_active") is not False:
        errors.append("Work must be inactive")
    label = payload.get("active_model_label")
    if not isinstance(label, str) or not PRO_TOKEN.search(label):
        errors.append("The active model label lacks a standalone Pro token")
    if isinstance(label, str) and re.search(r"\bWork\b|工作", label, re.IGNORECASE):
        errors.append("The active model label cannot come from Work")
    if payload.get("pro_control_selected") is not True:
        errors.append("No evidence proves the Pro option is selected")
    if payload.get("evidence_scope") != "active_model_control":
        errors.append("Evidence must come from the active model control")
    if payload.get("inspection_method") not in {"dom", "ax"}:
        errors.append("inspection_method must be dom or ax")
    if payload.get("selection_path") not in {"already_pro", "direct_option"}:
        errors.append("selection_path is invalid")
    observed = payload.get("observed_at")
    if not isinstance(observed, str):
        errors.append("observed_at must be an ISO-8601 string")
    else:
        try:
            parsed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                errors.append("observed_at must include a timezone")
        except ValueError:
            errors.append("observed_at is not a valid ISO-8601 timestamp")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate_json")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.gate_json).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("The gate record must be a JSON object")
        errors = validate_gate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors = [str(exc)]
    result = {"ok": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
