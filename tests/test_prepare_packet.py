#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "prepare_packet.py"
TASK_ID = "b53f8ed4-4711-471e-a588-79c65ce1845e"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PreparePacketTests(unittest.TestCase):
    def run_packet(self, project: Path, task_file: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(project),
                "--task-file",
                str(task_file),
                "--output-dir",
                str(output),
                "--task-id",
                TASK_ID,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_safe_packet_excludes_sensitive_and_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            project = base / "project"
            output = base / "out"
            project.mkdir()
            (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
            warning_fixture = "Contact owner" + "@" + "example.com\n"
            (project / "notes.txt").write_text(warning_fixture, encoding="utf-8")
            (project / "image.bin").write_bytes(b"\x00\x01\x02")
            env_fixture = "SECRET=" + "do-not-copy" + "\n"
            (project / ".env").write_text(env_fixture, encoding="utf-8")
            (project / "private.pem").write_text("not-a-real-key\n", encoding="utf-8")
            (project / "node_modules").mkdir()
            (project / "node_modules" / "pkg.js").write_text("ignored\n", encoding="utf-8")
            (project / "dist").mkdir()
            (project / "dist" / "bundle.js").write_text("ignored\n", encoding="utf-8")
            external = base / "outside.txt"
            external.write_text("outside\n", encoding="utf-8")
            (project / "outside-link").symlink_to(external)
            task_file = base / "TASK.md"
            task_file.write_text("# Safe task\n", encoding="utf-8")

            result = self.run_packet(project, task_file, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)

            zip_path = Path(summary["source_zip"])
            bundle_path = Path(summary["markdown_bundle"])
            manifest_path = Path(summary["manifest"])
            scan_path = Path(summary["safety_report"])
            self.assertEqual(summary["source_zip_sha256"], sha256(zip_path))

            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
                self.assertIn("TASK.md", names)
                self.assertIn("MANIFEST.json", names)
                self.assertIn("source/main.py", names)
                self.assertIn("source/notes.txt", names)
                self.assertNotIn("source/.env", names)
                self.assertNotIn("source/private.pem", names)
                self.assertNotIn("source/node_modules/pkg.js", names)
                self.assertNotIn("source/dist/bundle.js", names)
                self.assertNotIn("source/outside-link", names)
                self.assertNotIn("source/image.bin", names)
                self.assertTrue(all(not name.startswith("/") for name in names))

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_text = json.dumps(manifest, ensure_ascii=False)
            bundle_text = bundle_path.read_text(encoding="utf-8")
            self.assertNotIn(str(project), manifest_text)
            self.assertNotIn(str(project), bundle_text)
            self.assertEqual(manifest["artifacts"]["markdown_bundle"]["sha256"], sha256(bundle_path))
            scan = json.loads(scan_path.read_text(encoding="utf-8"))
            self.assertTrue(scan["ok"])
            self.assertGreaterEqual(scan["warning_count"], 1)

    def test_high_confidence_credential_blocks_sendable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            project = base / "project"
            output = base / "out"
            project.mkdir()
            (project / "config.txt").write_text(
                "OPENAI_API_KEY=sk-proj-" + "A" * 40 + "\n",
                encoding="utf-8",
            )
            task_file = base / "TASK.md"
            task_file.write_text("# Task\n", encoding="utf-8")

            result = self.run_packet(project, task_file, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Safety scan failed", result.stderr)
            self.assertFalse((output / f"{TASK_ID}-source.zip").exists())
            self.assertFalse((output / f"{TASK_ID}-bundle.md").exists())
            scan = json.loads((output / f"{TASK_ID}-safety.json").read_text(encoding="utf-8"))
            self.assertFalse(scan["ok"])
            self.assertGreaterEqual(scan["high_count"], 1)
            self.assertNotIn("sk-proj-", json.dumps(scan, ensure_ascii=False))

    def test_personal_absolute_path_blocks_packet(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            project = base / "project"
            output = base / "out"
            project.mkdir()
            personal_path = "/" + "Users/alice/private/file.txt"
            (project / "config.txt").write_text(f"fixture={personal_path}\n", encoding="utf-8")
            task_file = base / "TASK.md"
            task_file.write_text("# Task\n", encoding="utf-8")

            result = self.run_packet(project, task_file, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((output / f"{TASK_ID}-source.zip").exists())


if __name__ == "__main__":
    unittest.main()
