#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = SKILL_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


browser_gate = load_script("validate_browser_gate")
request_validator = load_script("validate_request")
reply_validator = load_script("validate_reply")


TASK_ID = "b53f8ed4-4711-471e-a588-79c65ce1845e"
MESSAGE_ID = "499075e3-9b27-4af2-9917-71d74f4a8bc9"
RESPONSE_ID = "d31f62d8-09c5-403b-a130-075406164f45"
MARKER = "[[PRO_COMMANDER_REPLY_5f76583c19f24abca8b00138776b3a43]]"


class BrowserGateTests(unittest.TestCase):
    def valid_gate(self) -> dict:
        return {
            "schema_version": 1,
            "surface": "iab",
            "chat_selected": True,
            "work_active": False,
            "active_model_label": "GPT Pro",
            "pro_control_selected": True,
            "evidence_scope": "active_model_control",
            "inspection_method": "dom",
            "selection_path": "already_pro",
            "observed_at": "2026-09-03T10:00:00+08:00",
        }

    def test_exact_pro_gate_passes(self) -> None:
        self.assertEqual(browser_gate.validate_gate(self.valid_gate()), [])

    def test_work_or_account_badge_cannot_pass(self) -> None:
        payload = self.valid_gate()
        payload["evidence_scope"] = "account_badge"
        self.assertTrue(browser_gate.validate_gate(payload))
        payload = self.valid_gate()
        payload["active_model_label"] = "GPT-5.4 Pro Work"
        self.assertTrue(browser_gate.validate_gate(payload))


class ReplyValidationTests(unittest.TestCase):
    def make_reply(self, phase: str = "PLAN", verdict: str = "NONE", iteration: int = 1) -> str:
        actions = {
            ("PLAN", "NONE"): "EXECUTE",
            ("REVIEW", "PASS"): "COMPLETE",
            ("REVIEW", "REVISE"): "REPAIR",
            ("REVIEW", "BLOCKED"): "STOP",
        }
        payload = {
            "protocol": "PRO_COMMANDER/1",
            "task_id": TASK_ID,
            "response_id": RESPONSE_ID,
            "in_reply_to": MESSAGE_ID,
            "phase": phase,
            "iteration": iteration,
            "verdict": verdict,
            "next_action": actions[(phase, verdict)],
            "reasoning_brief": "Decision based on the supplied evidence.",
            "plan_or_findings": ["Make the smallest complete change"],
            "acceptance_checks": ["Run unit tests"],
            "risks": [],
            "evidence_used": ["source.zip"],
        }
        return (
            "PRO_COMMANDER/1 RESPONSE\n\n```json\n"
            + json.dumps(payload, ensure_ascii=False)
            + "\n```\n\n"
            + MARKER
            + "\n"
        )

    def validate_text(self, text: str, phase: str, iteration: int) -> dict:
        payload = reply_validator.extract_payload(text, MARKER)
        return reply_validator.validate_payload(
            payload,
            task_id=TASK_ID,
            in_reply_to=MESSAGE_ID,
            phase=phase,
            iteration=iteration,
        )

    def test_plan_reply_and_unique_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            ledger = Path(raw) / "ledger.json"
            record = self.validate_text(self.make_reply(), "PLAN", 1)
            reply_validator.record_response(ledger, record)
            with self.assertRaises(reply_validator.ReplyError):
                reply_validator.record_response(ledger, record)

    def test_marker_must_be_last_line(self) -> None:
        with self.assertRaises(reply_validator.ReplyError):
            self.validate_text(self.make_reply() + "extra text\n", "PLAN", 1)

    def test_second_revision_is_not_automatic(self) -> None:
        text = self.make_reply(phase="REVIEW", verdict="REVISE", iteration=2)
        with self.assertRaises(reply_validator.ReplyError):
            self.validate_text(text, "REVIEW", 2)

    def test_marker_format_is_enforced(self) -> None:
        with self.assertRaises(reply_validator.ReplyError):
            reply_validator.extract_payload(self.make_reply(), "reply-complete")


class RequestValidationTests(unittest.TestCase):
    def make_request(self, phase: str = "PLAN", iteration: int = 1) -> str:
        payload = {
            "protocol": "PRO_COMMANDER/1",
            "task_id": TASK_ID,
            "message_id": MESSAGE_ID,
            "phase": phase,
            "iteration": iteration,
            "reply_marker": MARKER,
            "workspace": "sample-project",
            "objective": "Implement a small testable change",
            "acceptance_criteria": ["All unit tests pass"],
            "authorized_actions": ["Modify local files"],
            "forbidden_actions": ["Do not commit or deploy"],
            "known_facts": ["The working tree is readable"],
            "unknowns": [],
        }
        return "PRO_COMMANDER/1 REQUEST\n\n```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```\n"

    def test_plan_request_passes(self) -> None:
        payload = request_validator.extract_payload(self.make_request())
        record = request_validator.validate_payload(
            payload,
            task_id=TASK_ID,
            message_id=MESSAGE_ID,
            phase="PLAN",
            iteration=1,
        )
        self.assertEqual(record["reply_marker"], MARKER)

    def test_wrong_task_or_marker_fails(self) -> None:
        payload = request_validator.extract_payload(self.make_request())
        payload["reply_marker"] = "done"
        with self.assertRaises(request_validator.RequestError):
            request_validator.validate_payload(
                payload,
                task_id=TASK_ID,
                message_id=MESSAGE_ID,
                phase="PLAN",
                iteration=1,
            )


if __name__ == "__main__":
    unittest.main()
