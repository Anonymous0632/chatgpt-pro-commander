#!/usr/bin/env python3
"""Run deterministic skill-contract checks; this is not a live Pro test."""

from __future__ import annotations

import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEXT_FILES = [SKILL_ROOT / "SKILL.md", *sorted((SKILL_ROOT / "references").glob("*.md"))]
CORPUS = "\n".join(path.read_text(encoding="utf-8") for path in TEXT_FILES)

CHECKS = {
    "exact_pro_gate": lambda: all(token in CORPUS for token in ("exact `Pro`", "active_model_control", "Work")),
    "two_send_gates": lambda: all(token in CORPUS for token in ("PLAN", "REVIEW", "two sends")),
    "role_split": lambda: "technical commander" in CORPUS and "only local file writer" in CORPUS,
    "mode_disable": lambda: "fails closed as disabled" in CORPUS,
    "explicit_override": lambda: "explicit `$chatgpt-pro-commander`" in CORPUS,
    "per_task_bypass": lambda: "bypasses only the current task" in CORPUS and "without changing global state" in CORPUS,
    "unknown_no_resend": lambda: "UNKNOWN" in CORPUS and "Never resend" in CORPUS,
    "no_fallback": lambda: "Never silently fall back" in CORPUS and "API model" in CORPUS,
    "one_remediation": lambda: "one repair" in CORPUS and "ends as `BLOCKED`" in CORPUS,
    "credential_block": lambda: "blocks ZIP/bundle creation on high-confidence credentials" in CORPUS,
}


def main() -> int:
    payload = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    failures = []
    for item in payload["evals"]:
        failed = [name for name in item["contract_checks"] if name not in CHECKS or not CHECKS[name]()]
        print(("FAIL " if failed else "PASS ") + item["id"] + (": " + ", ".join(failed) if failed else ""))
        failures.extend(f"{item['id']}:{name}" for name in failed)
    print(f"SUMMARY total={len(payload['evals'])} failed={len(failures)} mode=static-contract")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
