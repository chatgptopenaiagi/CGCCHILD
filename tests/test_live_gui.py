"""Q6 Windows desktop continuity workflows using real external temporary stores."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QEvent
from cgcchild.gui import create_window, PAGES


class LiveGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["CGC-live-GUI-test"])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cgc-live-gui-")
        self.base = Path(self.tmp.name)
        self.project = self.base / "project"
        self.project.mkdir()
        self.store = self.base / "sessions"
        subprocess.run(["git", "init", "-q", str(self.project)], check=True, capture_output=True, timeout=15)
        self.windows = []

    def window(self):
        window = create_window()
        self.windows.append(window)
        window.project_edit.setText(str(self.project))
        window.store_edit.setText(str(self.store))
        return window

    def wait(self, window):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            self.app.processEvents()
            if window.live_job is None:
                break
            time.sleep(0.01)
        self.assertIsNone(window.live_job, "bounded GUI operation did not finish")
        window.live_timer.stop()

    def start(self, window):
        window.start_live()
        self.wait(window)
        self.assertIsNotNone(window.live_session, window.live_hint.text())
        self.assertEqual(window.live_session.summary()["state"], "RUNNING")

    def tearDown(self):
        for window in self.windows:
            self.wait(window)
            window.close()
            self.wait(window)
            window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.tmp.cleanup()

    def test_all_pages_and_explicit_start_boundary(self):
        with patch("cgcchild.live.Session.start", side_effect=AssertionError("implicit session forbidden")):
            window = self.window()
            self.assertEqual(len(PAGES), 18)
            self.assertFalse(self.store.exists())
            self.assertFalse(window.live_timer.isActive())
            for index, page in enumerate(PAGES):
                window.navigation.setCurrentRow(index)
                self.assertEqual(window.stack.currentIndex(), index)
                self.assertTrue(window.views[page].toPlainText())
            window.example()
            self.assertIn("SYNTHETIC", window.views["Logs"].toPlainText())
            self.assertIn("UNKNOWN", window.views["Live Session"].toPlainText())

    def test_live_observe_checkpoint_preserve_and_historical_reopen(self):
        window = self.window()
        self.start(window)
        self.assertIn(str(window.live_session.path), window.live_metrics.text())
        (self.project / "work.txt").write_text("first change", encoding="utf-8")
        window.observe_live()
        self.wait(window)
        window.live_session.report("ERROR_OBSERVED", {"error_id": "e1", "message": "synthetic error"})
        window.live_session.report("DECISION_DECLARED", {"text": "Keep evidence outside the project"})
        window.live_session.report("NEXT_ACTION_DECLARED", {"text": "Review unfinished work"})
        window.refresh()
        self.assertIn("FILESYSTEM_CHANGE_OBSERVED", window.views["Timeline"].toPlainText())
        self.assertIn("REPORTED", window.views["Errors"].toPlainText())
        self.assertIn("UNKNOWN", window.views["Evidence"].toPlainText())
        window.checkpoint_live()
        self.wait(window)
        self.assertGreater(window.live_session.summary()["checkpoint_count"], 0)
        window.preserve_live()
        self.wait(window)
        self.assertEqual(window.live_session.summary()["state"], "PRESERVED")
        capsules = list(window.live_session.path.rglob("*.cgcpack"))
        self.assertTrue(capsules)
        fresh = self.window()
        fresh.load_path(capsules[-1])
        fresh.refresh()
        self.assertIn("HISTORICAL_ONLY", fresh.views["Timeline"].toPlainText())
        self.assertIn("UNKNOWN", fresh.views["Capsules"].toPlainText())
        self.assertFalse(fresh.live_timer.isActive())
        self.assertIsNone(fresh.live_session)
        self.assertEqual((self.project / "work.txt").read_text(), "first change")

    def test_close_records_interruption_and_resume_links_generation(self):
        window = self.window()
        self.start(window)
        session_path = window.live_session.path
        generation = window.live_session.summary()["generation"]
        window.close()
        self.wait(window)
        self.assertEqual(window.live_session.summary()["state"], "INTERRUPTED")
        fresh = self.window()
        fresh.resume_live_path(session_path)
        self.wait(fresh)
        self.assertEqual(fresh.live_session.summary()["generation"], generation + 1)
        self.assertIn("SESSION_RESUMED", fresh.views["Timeline"].toPlainText())

    def test_imported_markup_and_failed_launch_remain_inert(self):
        window = self.window()
        self.start(window)
        window.live_session.report("DECISION_DECLARED", {"text": "<script>never_run()</script>"})
        window.refresh()
        self.assertIn("<script>never_run()</script>", window.views["Timeline"].toPlainText())
        window.run_live("Unavailable worker", lambda: (_ for _ in ()).throw(OSError("private diagnostic")))
        self.wait(window)
        self.assertIn("UNKNOWN", window.views["Logs"].toPlainText())
        self.assertNotIn("private diagnostic", window.views["Logs"].toPlainText())
        self.assertEqual(window.live_session.summary()["state"], "RUNNING")
        window.checkpoint_live()
        self.wait(window)
        self.assertGreater(window.live_session.summary()["checkpoint_count"], 0)

    def test_explicit_smoke_reopens_live_capsule_in_fresh_gui_process(self):
        window = self.window()
        self.start(window)
        window.preserve_live()
        self.wait(window)
        capsule = window.live_session.path / "capsules" / "final.cgcpack"
        screenshot = self.base / "fresh-live-gui.png"
        env = dict(os.environ, CGC_SMOKE_LIVE_CAPSULE=str(capsule), QT_QPA_PLATFORM="offscreen")
        result = subprocess.run([sys.executable, "-m", "cgcchild", "gui", "--smoke-output", str(screenshot)],
                                env=env, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertTrue(screenshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_smoke_capsule_environment_is_ignored_by_normal_window(self):
        with patch.dict(os.environ, {"CGC_SMOKE_LIVE_CAPSULE": str(self.base / "never-read.cgcpack")}), \
                patch("cgcchild.live.open_capsule", side_effect=AssertionError("implicit import forbidden")):
            window = self.window()
            self.assertIsNone(window.live_history)


if __name__ == "__main__":
    unittest.main()
