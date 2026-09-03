#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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


dispatch = load_script("dispatch_state")
mode = load_script("mode_control")


TASK_ID = "b53f8ed4-4711-471e-a588-79c65ce1845e"
MESSAGE_ID = "499075e3-9b27-4af2-9917-71d74f4a8bc9"


class DispatchStateTests(unittest.TestCase):
    def test_not_sent_unknown_sent_and_duplicate_protection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = Path(raw) / "dispatch.json"
            state = dispatch.execute(state_path, "init", TASK_ID, MESSAGE_ID, None)
            self.assertEqual(state["state"], "NOT_SENT")
            self.assertTrue(dispatch.execute(state_path, "can-send", TASK_ID, MESSAGE_ID, None)["can_send"])

            armed = dispatch.execute(state_path, "arm", TASK_ID, MESSAGE_ID, None)
            self.assertEqual(armed["state"], "UNKNOWN")
            self.assertEqual(armed["send_attempts"], 1)
            self.assertFalse(dispatch.execute(state_path, "can-send", TASK_ID, MESSAGE_ID, None)["can_send"])
            with self.assertRaises(dispatch.DispatchError):
                dispatch.execute(state_path, "arm", TASK_ID, MESSAGE_ID, None)

            sent = dispatch.execute(state_path, "mark-sent", TASK_ID, MESSAGE_ID, None)
            self.assertEqual(sent["state"], "SENT")
            with self.assertRaises(dispatch.DispatchError):
                dispatch.execute(state_path, "mark-sent", TASK_ID, MESSAGE_ID, None)

    def test_unknown_state_keeps_original_conversation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = Path(raw) / "dispatch.json"
            dispatch.execute(state_path, "init", TASK_ID, MESSAGE_ID, None)
            dispatch.execute(
                state_path,
                "set-conversation",
                TASK_ID,
                MESSAGE_ID,
                "https://chatgpt.com/c/existing",
            )
            armed = dispatch.execute(state_path, "arm", TASK_ID, MESSAGE_ID, None)
            self.assertEqual(armed["conversation_url"], "https://chatgpt.com/c/existing")
            self.assertEqual(armed["state"], "UNKNOWN")


class ModeControlTests(unittest.TestCase):
    def test_fail_closed_enable_pause_resume_disable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = Path(raw) / "mode.json"
            missing = mode.load_state(state_path)
            self.assertEqual(missing["mode"], "disabled")
            enabled = mode.atomic_write(state_path, "enabled")
            self.assertEqual(enabled["mode"], "enabled")
            paused = mode.atomic_write(state_path, "paused")
            self.assertEqual(paused["mode"], "paused")
            resumed = mode.atomic_write(state_path, "enabled")
            self.assertEqual(resumed["mode"], "enabled")
            disabled = mode.atomic_write(state_path, "disabled")
            self.assertEqual(disabled["mode"], "disabled")


if __name__ == "__main__":
    unittest.main()
