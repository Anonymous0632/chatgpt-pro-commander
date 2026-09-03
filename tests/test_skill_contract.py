#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_required_layout(self) -> None:
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "evals/evals.json",
            "references/attachment-policy.md",
            "references/global-agents-snippet.md",
            "references/model-and-browser-gates.md",
            "references/recovery-and-reporting.md",
            "references/task-protocol.md",
            "references/usage.md",
            "scripts/dispatch_state.py",
            "scripts/mode_control.py",
            "scripts/prepare_packet.py",
            "scripts/validate_browser_gate.py",
            "scripts/validate_request.py",
            "scripts/validate_reply.py",
        ]
        for relative in required:
            self.assertTrue((SKILL_ROOT / relative).is_file(), relative)

    def test_frontmatter_has_only_name_and_description(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(match)
        keys = []
        for line in match.group(1).splitlines():
            if line and not line.startswith((" ", "\t")) and ":" in line:
                keys.append(line.split(":", 1)[0])
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("$chatgpt-pro-commander", match.group(1))

    def test_no_personal_absolute_paths(self) -> None:
        personal_prefix = "/" + "Users/"
        for path in SKILL_ROOT.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            self.assertNotIn(personal_prefix, text, str(path.relative_to(SKILL_ROOT)))

    def test_eval_schema_and_unique_ids(self) -> None:
        payload = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        evals = payload["evals"]
        self.assertGreaterEqual(len(evals), 8)
        ids = [item["id"] for item in evals]
        self.assertEqual(len(ids), len(set(ids)))
        for item in evals:
            self.assertTrue(item["scenario"])
            self.assertTrue(item["expected"])
            self.assertTrue(item["contract_checks"])

    def test_openai_yaml_interface_contract(self) -> None:
        text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        short = re.search(r'^  short_description: "([^"]+)"$', text, flags=re.MULTILINE)
        prompt = re.search(r'^  default_prompt: "([^"]+)"$', text, flags=re.MULTILINE)
        self.assertIsNotNone(short)
        self.assertIsNotNone(prompt)
        self.assertGreaterEqual(len(short.group(1)), 25)
        self.assertLessEqual(len(short.group(1)), 64)
        self.assertIn("$chatgpt-pro-commander", prompt.group(1))
        self.assertIn("allow_implicit_invocation: true", text)


if __name__ == "__main__":
    unittest.main()
