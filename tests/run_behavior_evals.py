#!/usr/bin/env python3
"""对 Skill 文本执行确定性的行为契约评测；不冒充真实 Pro 端到端测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEXT_FILES = [SKILL_ROOT / "SKILL.md", *sorted((SKILL_ROOT / "references").glob("*.md"))]
CORPUS = "\n".join(path.read_text(encoding="utf-8") for path in TEXT_FILES)


CHECKS = {
    "exact_pro_gate": lambda: all(
        token in CORPUS for token in ("精确 `Pro` 模式", "active_model_control", "Work/工作")
    ),
    "two_send_gates": lambda: "PLAN" in CORPUS
    and "REVIEW" in CORPUS
    and "两次发送确认" in CORPUS,
    "role_split": lambda: "ChatGPT Pro" in CORPUS and "Codex" in CORPUS and "唯一的本地写入者" in CORPUS,
    "mode_disable": lambda: "工作流为启用状态" in CORPUS and "状态文件缺失或损坏时默认视为停用" in CORPUS,
    "explicit_override": lambda: "显式 `$chatgpt-pro-commander`" in CORPUS,
    "per_task_bypass": lambda: "本次不使用 Pro" in CORPUS and "不改写全局状态" in CORPUS,
    "unknown_no_resend": lambda: "UNKNOWN" in CORPUS and "禁止再次发送" in CORPUS,
    "no_fallback": lambda: "禁止静默换用其他模型" in CORPUS and "API 模型" in CORPUS,
    "one_remediation": lambda: "一次自动修正" in CORPUS and "第二次仍非 `PASS`" in CORPUS,
    "credential_block": lambda: "发现高危凭据或个人绝对路径时退出且不生成 ZIP/Bundle" in CORPUS,
}


def main() -> int:
    payload = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    for item in payload["evals"]:
        failed = [name for name in item["contract_checks"] if name not in CHECKS or not CHECKS[name]()]
        if failed:
            failures.append(f"{item['id']}: {', '.join(failed)}")
            print(f"FAIL {item['id']}: {', '.join(failed)}")
        else:
            print(f"PASS {item['id']}")
    print(f"SUMMARY total={len(payload['evals'])} failed={len(failures)} mode=static-contract")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
