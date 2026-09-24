"""Render the real Live Session page from an owned Windows fixture, then preserve it."""
import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QBuffer, QCoreApplication, QEvent, QIODevice
from PySide6.QtWidgets import QApplication
from cgcchild.core import save_new
from cgcchild.gui import create_window, PAGES
from cgcchild.live import Session, open_capsule


def git(project, *arguments):
    completed = subprocess.run(["git", "-C", str(project), "-c", "core.hooksPath=NUL", *arguments],
                               capture_output=True, check=True, timeout=20)
    return completed.stdout.decode("utf-8", "replace").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--capsule", required=True)
    args = parser.parse_args()
    app = QApplication.instance() or QApplication(["CGC-live-preview"])
    with tempfile.TemporaryDirectory(prefix="cgc-live-preview-") as folder:
        base = Path(folder)
        project = base / "Windows example project"
        project.mkdir()
        git(project, "init", "-b", "main")
        git(project, "config", "user.name", "CGC Windows preview fixture")
        git(project, "config", "user.email", "preview@example.invalid")
        (project / "README.md").write_text("Owned Windows preview project.\n", encoding="utf-8")
        git(project, "add", "README.md")
        git(project, "commit", "-m", "Create owned preview fixture")
        session = Session.start(project, base / "sessions", worker_type="Codex adapter / preview fixture")
        (project / "README.md").write_text("Owned Windows preview project.\nLive change observed.\n", encoding="utf-8")
        (project / "test_preview.py").write_text(
            "import unittest\nclass PreviewTests(unittest.TestCase):\n"
            "    def test_arithmetic(self): self.assertEqual(2 + 2, 4)\n"
            "    def test_text(self): self.assertEqual('CGC'.lower(), 'cgc')\n", encoding="utf-8")
        session.report("FILE_EDIT_REPORTED", {"paths": ["README.md", "test_preview.py"]})
        session.observe()
        session.run_test([sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_preview.py"])
        session.report("DECISION_DECLARED", {"text": "Preserve engineering evidence outside the observed project."})
        session.report("NEXT_ACTION_DECLARED", {"text": "Review the saved capsule in a fresh CGC process.",
                       "dependencies": ["Durable session capsule"], "preconditions": ["Independent review"]})
        session.checkpoint()
        window = create_window()
        window.started_live(session)
        window.live_timer.stop()
        window.refresh()
        window.navigation.setCurrentRow(PAGES.index("Live Session"))
        window.resize(1240, 960)
        window.show()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            app.processEvents()
            if window.live_job is None:
                break
            time.sleep(0.01)
        if window.live_job is not None:
            raise RuntimeError("PREVIEW_DISCOVERY_TIMEOUT")
        window.live_hint.setText("Real temporary Windows project observation and two passing unittest tests.\n"
                                "Remote publication remains UNKNOWN. This preview uses no production project.")
        app.processEvents()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not window.grab().save(buffer, "PNG"):
            raise RuntimeError("PREVIEW_RENDER_FAILED")
        save_new(args.output, bytes(buffer.data()))
        capsule_path = session.preserve()
        raw = capsule_path.read_bytes()
        reopened = open_capsule(raw)
        if reopened["authority"] != "HISTORICAL_ONLY":
            raise RuntimeError("PREVIEW_CAPSULE_AUTHORITY_FAILED")
        save_new(args.capsule, raw)
        window.refresh()
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        print(json.dumps({"state": "PASSED", "screenshot": str(Path(args.output).resolve()),
                          "capsule": str(Path(args.capsule).resolve()), "session_state": "PRESERVED",
                          "test_verification": session.summary()["tests"][-1].get("verification_state"),
                          "historical_authority": reopened["authority"]}))


if __name__ == "__main__":
    main()
