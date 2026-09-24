"""Local desktop consumer. Imported text is always rendered as plain text."""
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from . import __version__, sdk
from .core import Workbench, read_input, save_new, security_debt, resource
from .execution import Mode, DryRunExecutor, SimulationExecutor

PAGES = ("Dashboard", "Project Status", "Evidence", "Continuity", "Safe Resume",
         "Reports", "Capsules", "Recovery Review", "Plugin / SDK Status",
         "Security Debt", "System Information", "Logs", "About", "Live Session",
         "Timeline", "Git", "Tests", "Errors")

# A caller may release its Python window reference immediately after close().
# Keep a deferred close alive until its owned operation finishes and is journaled.
_PENDING_WINDOWS = set()


def create_window(mode=Mode.READ_ONLY_SAFE):
    from PySide6.QtCore import QThread, QTimer
    from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
        QListWidget, QStackedWidget, QPlainTextEdit, QPushButton, QFileDialog, QMessageBox,
        QComboBox, QLineEdit, QInputDialog)
    from .live import Session, discover_sessions, open_capsule, default_store

    class LiveOperation(QThread):
        """Keep bounded project I/O off the desktop event loop; one operation at a time."""
        def __init__(self, operation, parent):
            super().__init__(parent)
            self.operation = operation
            self.result = None
            self.failed = False

        def run(self):
            try:
                self.result = self.operation()
            except Exception:
                # Files, commands and OS exceptions can contain sensitive text.
                self.failed = True

    class Window(QMainWindow):
        def __init__(self):
            super().__init__()
            self.model = Workbench(mode)
            self.live_session = None
            self.live_state = "IDLE"
            self.live_history = None
            self.live_job = None
            self.live_callback = None
            self.live_action = ""
            self.close_requested = False
            self.close_record_attempted = False
            self.polls_since_checkpoint = 0
            self.live_timer = QTimer(self)
            self.live_timer.setInterval(5000)
            self.live_timer.timeout.connect(self.poll_live)
            self.log = ["Started in " + mode.value + ". No project or account was scanned."]
            self.setWindowTitle("CREDID GUARDIAN CODEX")
            self.resize(1120, 780)
            root = QWidget()
            self.setCentralWidget(root)
            layout = QVBoxLayout(root)
            brand = QLabel("CREDID GUARDIAN CODEX")
            brand.setStyleSheet("font-size:25px;font-weight:700;color:#0f766e;padding:12px 0")
            layout.addWidget(brand)
            self.banner = QLabel()
            self.banner.setWordWrap(True)
            self.banner.setStyleSheet("background:#fff4d6;color:#654900;padding:12px;border-radius:6px")
            layout.addWidget(self.banner)
            toolbar = QHBoxLayout()
            layout.addLayout(toolbar)
            for text, callback in (("Open snapshot / capsule", self.open_file),
                                   ("Load synthetic example", self.example),
                                   ("Export capsule", self.export_capsule),
                                   ("Export HTML report", self.export_report)):
                button = QPushButton(text)
                button.clicked.connect(callback)
                toolbar.addWidget(button)
            self.mode_box = QComboBox()
            self.mode_box.addItems([m.value for m in Mode])
            self.mode_box.setCurrentText(mode.value)
            self.mode_box.currentTextChanged.connect(self.change_mode)
            toolbar.addWidget(self.mode_box)
            body = QHBoxLayout()
            layout.addLayout(body, 1)
            self.navigation = QListWidget()
            self.navigation.addItems(PAGES)
            self.navigation.setFixedWidth(220)
            self.stack = QStackedWidget()
            self.views = {}
            for page in PAGES:
                widget = QWidget()
                page_layout = QVBoxLayout(widget)
                title = QLabel(page)
                title.setStyleSheet("font-size:22px;font-weight:600;padding:10px 0")
                page_layout.addWidget(title)
                if page == "Live Session":
                    self.add_live_controls(page_layout)
                view = QPlainTextEdit()
                view.setReadOnly(True)
                view.setAccessibleName(page + " details")
                self.views[page] = view
                page_layout.addWidget(view)
                if page == "Recovery Review":
                    for text, callback in (("Dry-run checkpoint plan", self.dry_run),
                                           ("Simulate checkpoint (explicit simulation mode)", self.simulate)):
                        button = QPushButton(text)
                        button.clicked.connect(callback)
                        page_layout.addWidget(button)
                self.stack.addWidget(widget)
            body.addWidget(self.navigation)
            body.addWidget(self.stack, 1)
            self.navigation.currentRowChanged.connect(self.stack.setCurrentIndex)
            self.navigation.setCurrentRow(0)
            self.setStyleSheet("QMainWindow{background:#f4f7f8} QListWidget,QPlainTextEdit{background:white;border:1px solid #d6e1e4;padding:8px;font-size:14px} QPushButton{padding:9px} QLabel{color:#18333b}")
            self.refresh()
            QTimer.singleShot(0, self.discover_live_on_start)

        def add_live_controls(self, layout):
            self.live_status = QLabel("IDLE — select an explicit project to begin")
            self.live_status.setWordWrap(True)
            self.live_status.setStyleSheet("font-size:18px;font-weight:600;color:#0f766e")
            layout.addWidget(self.live_status)
            self.live_metrics = QLabel("No project is being observed.")
            self.live_metrics.setWordWrap(True)
            layout.addWidget(self.live_metrics)
            self.discovery_label = QLabel("Only CGC's selected session store is checked for unclosed sessions.")
            self.discovery_label.setWordWrap(True)
            layout.addWidget(self.discovery_label)
            self.project_edit = QLineEdit()
            self.project_edit.setAccessibleName("Live project directory")
            self.project_edit.setPlaceholderText("Select the project CGC may observe")
            self.project_edit.setMaxLength(32768)
            self.store_edit = QLineEdit(str(default_store()))
            self.store_edit.setAccessibleName("Session storage directory")
            self.store_edit.setMaxLength(32768)
            self.live_selectors = []
            for name, field, callback in (("Project", self.project_edit, self.select_project),
                                           ("Session store", self.store_edit, self.select_store)):
                row = QHBoxLayout()
                row.addWidget(QLabel(name))
                row.addWidget(field, 1)
                button = QPushButton("Select directory")
                button.clicked.connect(callback)
                self.live_selectors.append(button)
                row.addWidget(button)
                layout.addLayout(row)
            self.live_buttons = {}
            for controls in ((("Start guarded session", self.start_live),
                              ("Observe now", self.observe_live),
                              ("Checkpoint now", self.checkpoint_live),
                              ("End & preserve", self.preserve_live)),
                             (("Resume interrupted session", self.resume_live),
                              ("Launch Codex", self.launch_live),
                              ("Verify remote ref", self.verify_live))):
                row = QHBoxLayout()
                for title, callback in controls:
                    button = QPushButton(title)
                    button.clicked.connect(callback)
                    self.live_buttons[title] = button
                    row.addWidget(button)
                layout.addLayout(row)
            self.live_hint = QLabel("Observer-only sessions work without Codex. Polling runs while this window is open.\n"
                                   "Checkpoint preserves evidence in the session store. Production repository mutation stays disabled.")
            self.live_hint.setWordWrap(True)
            layout.addWidget(self.live_hint)

        def select_project(self):
            path = QFileDialog.getExistingDirectory(self, "Select the explicit project root", self.project_edit.text())
            if path:
                self.project_edit.setText(path)

        def select_store(self):
            path = QFileDialog.getExistingDirectory(self, "Select storage outside the observed project", self.store_edit.text())
            if path:
                self.store_edit.setText(path)

        def discover_live_on_start(self):
            if self.close_requested:
                return
            selected_store = self.store_edit.text().strip() or None
            def discovered(items):
                current_id = self.live_session.summary().get("session_id") if self.live_session else None
                count = sum(bool(item.get("recovery_candidate")) and item.get("session_id") != current_id for item in items)
                self.discovery_label.setText((str(count) + " unclosed session(s) need recovery review; another foreground owner may be active. "
                                              "Use Resume interrupted session to select the exact stored session.") if count else
                                             ("No other unclosed sessions found in the selected CGC store." if current_id else
                                              "No unclosed sessions found in the selected CGC store."))
            self.run_live("Check CGC session store", lambda: discover_sessions(selected_store), discovered)

        def run_live(self, action, operation, callback=None):
            if self.live_job is not None:
                return
            self.live_action = action
            self.live_callback = callback
            self.live_job = LiveOperation(operation, self)
            _PENDING_WINDOWS.add(self)
            self.live_job.finished.connect(self.finish_live_operation)
            self.live_hint.setText(action + "…")
            self.live_job.start()
            self.refresh_live_controls()

        def finish_live_operation(self):
            job = self.live_job
            # finished can precede native thread-local cleanup on Windows.
            # Join before its parent window or Python wrapper may be released.
            job.wait()
            callback = self.live_callback
            self.live_job = None
            self.live_callback = None
            if job.failed:
                if self.live_action == "Launch Codex in the selected project" and self.active_live():
                    self.live_timer.start()
                    self.live_hint.setText("Codex launch is unavailable. The observer-only session continues; structured events can be supplied separately.")
                else:
                    self.live_timer.stop()
                    self.live_hint.setText("Operation refused or unavailable. Observation paused; saved history is retained. Review the selected project and session store.")
                self.log.append(self.live_action + ": REFUSED / UNKNOWN. No diagnostic contents were stored.")
            else:
                self.live_hint.setText(self.live_action + " completed. Evidence grades and uncertainty remain visible.")
                self.log.append(self.live_action + " completed.")
                if callback is not None:
                    callback(job.result)
            job.deleteLater()
            self.refresh()
            if self.close_requested:
                self.close()
            if self.live_job is None:
                _PENDING_WINDOWS.discard(self)

        def active_live(self):
            return self.live_session is not None and self.live_state == "RUNNING"

        def refresh_live_controls(self):
            busy = self.live_job is not None
            active = self.active_live()
            for label, button in self.live_buttons.items():
                allowed = not active if label in ("Start guarded session", "Resume interrupted session") else active
                button.setEnabled(not busy and allowed)
            self.project_edit.setReadOnly(active or busy)
            self.store_edit.setReadOnly(active or busy)
            for selector in self.live_selectors:
                selector.setEnabled(not active and not busy)

        def start_live(self):
            if self.active_live():
                return
            project = self.project_edit.text().strip()
            store = self.store_edit.text().strip()
            if not project:
                self.live_hint.setText("Select the explicit project directory first.")
                return
            self.run_live("Start guarded session", lambda: Session.start(project, store or None), self.started_live)

        def started_live(self, session):
            self.live_session = session
            self.live_state = session.summary().get("state", "UNKNOWN")
            self.project_edit.setText(str(session.summary().get("project_root", "")))
            self.store_edit.setText(str(session.path.parent))
            self.live_history = None
            self.close_record_attempted = False
            self.polls_since_checkpoint = 0
            self.live_timer.start()
            self.navigation.setCurrentRow(PAGES.index("Live Session"))

        def observe_live(self):
            if self.active_live():
                self.run_live("Observe selected project", self.live_session.observe)

        def verify_live(self):
            if self.active_live():
                self.run_live("Verify live remote ref", lambda: self.live_session.observe(verify_remote=True))

        def checkpoint_live(self):
            if self.active_live():
                self.run_live("Preserve evidence checkpoint", self.live_session.checkpoint,
                              lambda _: setattr(self, "polls_since_checkpoint", 0))

        def poll_live(self):
            if self.live_job is not None or not self.active_live():
                return
            self.polls_since_checkpoint += 1
            if self.polls_since_checkpoint >= 12:
                self.checkpoint_live()
            else:
                self.observe_live()

        def preserve_live(self):
            if self.active_live():
                self.live_timer.stop()
                self.run_live("End and preserve session capsule", self.live_session.preserve,
                              lambda path: self.live_hint.setText("Session capsule: " + str(path) + "\nHistorical evidence grants no current execution authority."))

        def resume_live(self):
            if self.active_live():
                return
            selected_store = self.store_edit.text().strip() or None
            def choose(items):
                candidates = [item for item in items if item.get("recovery_candidate")
                              or item.get("state") not in ("PRESERVED", "CLOSED_WITH_UNKNOWN")]
                if not candidates:
                    self.live_hint.setText("No interrupted session found in the selected CGC store.")
                    return
                labels = [str(index + 1) + ". " + str(item.get("session_id", "UNKNOWN")) + " | "
                          + str(item.get("state", "UNKNOWN")) + " | "
                          + str(item.get("storage_path", item.get("path", "UNKNOWN")))
                          for index, item in enumerate(candidates)]
                label, accepted = QInputDialog.getItem(self, "Resume as a new generation", "Stored session", labels, 0, False)
                if accepted:
                    item = candidates[labels.index(label)]
                    self.resume_live_path(item.get("storage_path") or item.get("path"))
            self.run_live("Find interrupted CGC sessions", lambda: discover_sessions(selected_store), choose)

        def resume_live_path(self, path):
            def recover():
                session = Session.open(path)
                session.recover()
                session.resume()
                return session
            self.run_live("Recover and resume as a new generation", recover, self.started_live)

        def launch_live(self):
            if self.active_live():
                from .live.adapter import launch_codex
                self.run_live("Launch Codex in the selected project", lambda: launch_codex(self.live_session))

        def display(self, page, value):
            self.views[page].setPlainText(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True))

        def refresh(self):
            status = self.model.status()
            self.banner.setText("EXPERIMENTAL  |  " + self.model.mode.value + "  |  Current safety: UNKNOWN  |  Production mutation: DISABLED")
            self.display("Dashboard", "THE GUARDIAN OBSERVES. CODEX PRESERVES.\n\n"
                         + ("Historical snapshot loaded. Review its uncertainty before acting." if status["snapshot_loaded"] else "Open a reviewed JSON snapshot or .cgcpack to begin.\nThe synthetic example is available for an offline tour.")
                         + "\n\nLive Continuity: select Live Session to observe an explicit project.\nNo quota account is polled. Remote verification is explicit.\nExports contain historical evidence, never execution authority.")
            self.display("Project Status", status)
            self.display("Evidence", self.model.evidence())
            self.display("Security Debt", security_debt())
            self.display("System Information", {"system": platform.system(), "release": platform.release(),
                         "python": platform.python_version(), "product_version": __version__, "network_listener": False})
            self.display("Plugin / SDK Status", {"plugin": "DISTRIBUTABLE / NOT AUTO-INSTALLED",
                         "python_sdk": sdk.negotiate(sdk.API_VERSION), "node_sdk": "Bundled separately in sdk/javascript",
                         "host_interoperability": "PARTIAL / structured events require explicit integration",
                         "local_service": "Foreground MCP; explicit historical input or live session required",
                         "automatic_codex_lifecycle_hooks": "UNKNOWN; observer-only fallback available"})
            self.display("Reports", "Export an inert HTML report using the toolbar.\nReports retain historical labels and UNKNOWN safety.\nAn existing file is never overwritten.")
            self.display("Capsules", "Open / export historical .cgcpack using the toolbar.\nEnd & preserve creates a live session capsule in its external session store.\nArchives are validated in memory; no archive member is extracted.\nSource files, Git objects and current authority are not included.")
            self.display("About", "CREDID GUARDIAN CODEX\nCGCCHILD " + __version__ + " — experimental Windows release\n\nApache-2.0\nOriginal author: Mihai-Bogdan Simion\n\nONE SENSOR. MULTIPLE CONSUMERS.\n\nQt / PySide6 is dynamically bundled; see THIRD_PARTY_NOTICES.md and licenses in the portable package.")
            if status["snapshot_loaded"]:
                self.display("Continuity", status["summary"])
                self.display("Safe Resume", self.model.review())
                self.display("Recovery Review", self.model.review())
            else:
                for page in ("Continuity", "Safe Resume", "Recovery Review"):
                    self.display(page, "No snapshot selected. Current safety remains UNKNOWN.")
            self.display("Logs", "\n".join(self.log[-100:]))
            self.refresh_live()

        def refresh_live(self):
            if self.live_job is not None:
                self.refresh_live_controls()
                return
            if self.live_session is not None:
                summary = self.live_session.summary()
                self.live_state = summary.get("state", "UNKNOWN")
                timeline = self.live_session.events()
                authority = "OBSERVED_SESSION_HISTORY / NO_EXECUTION_AUTHORITY"
            elif self.live_history is not None:
                summary = self.live_history["session"]
                timeline = self.live_history["timeline"]
                authority = "HISTORICAL_ONLY / CURRENT_AUTHORITY_UNKNOWN"
            else:
                summary = None
                timeline = []
                authority = "NO_SESSION_SELECTED"
            if summary is None:
                self.live_status.setText("IDLE — select an explicit project to begin")
                self.live_metrics.setText("No project is being observed. Storage: " + self.store_edit.text())
                self.display("Live Session", {"state": "IDLE", "storage_base": self.store_edit.text(),
                             "observation": "Explicit project selection required", "filesystem_exclusivity": "UNKNOWN",
                             "production_mutation": "DISABLED", "confidence": "UNKNOWN"})
                for page in ("Timeline", "Git", "Tests", "Errors"):
                    self.display(page, "No session selected. REPORTED, OBSERVED and VERIFIED are distinct.\nMissing evidence remains UNKNOWN.")
            else:
                self.live_status.setText(str(summary.get("state", "UNKNOWN")) + "  |  generation "
                                         + str(summary.get("generation", "UNKNOWN")) + "  |  confidence "
                                         + str(summary.get("confidence", "PARTIAL")))
                tests = summary.get("tests", [])
                errors = summary.get("errors", [])
                commits = summary.get("commits", [])
                observed_commits = {item.get("sha") for item in commits
                                    if item.get("evidence_grade") in ("OBSERVED", "VERIFIED") and item.get("sha")}
                latest_test = next((item for item in reversed(tests) if item.get("evidence_grade") != "REPORTED"
                                    and item.get("verification_state")), None)
                test_status = "UNKNOWN"
                if latest_test is not None:
                    test_status = str(latest_test["verification_state"]) + " (" + " / ".join(
                        str(latest_test.get("parsed_" + key)) + " " + key if latest_test.get("parsed_" + key) is not None
                        else key + " UNKNOWN" for key in ("passed", "failed", "skipped")) + ")"
                duration = "UNKNOWN"
                try:
                    start = datetime.fromisoformat(summary["start_time"])
                    end = datetime.fromisoformat(summary["end_time"]) if summary.get("end_time") else (
                        datetime.now(timezone.utc) if self.live_session is not None else None)
                    if end is not None:
                        seconds = max(0, int((end - start).total_seconds()))
                        duration = f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"
                except (ValueError, TypeError, KeyError):
                    pass
                changed = summary.get("files_changed", "UNKNOWN")
                if isinstance(changed, list):
                    changed = len(changed)
                open_errors = sum(1 for error in errors if error.get("status") == "OPEN") if isinstance(errors, list) else "UNKNOWN"
                self.live_metrics.setText("Files changed: " + str(changed) + "  |  Test attempts: "
                                          + str(len(tests)) + "  |  Observed commits: " + str(len(observed_commits))
                                          + "  |  Open errors: " + str(open_errors)
                                          + "\nLatest test: " + test_status + "  |  Push verification: " + str(summary.get("push_verification", "UNKNOWN"))
                                          + "\nCheckpoints: " + str(summary.get("checkpoint_count", "UNKNOWN"))
                                          + "  |  Events: " + str(summary.get("event_count", len(timeline)))
                                          + "  |  Duration: " + duration
                                          + "\nSession storage: " + str(summary.get("storage_path", "HISTORICAL_ONLY")))
                session_fields = ("session_id", "project_root", "worker_type", "worker_version", "start_time",
                                  "end_time", "push_verification", "last_checkpoint", "next_action", "unfinished_work",
                                  "current_authority", "filesystem_exclusivity", "mutation_authorized", "preservation_complete")
                self.display("Live Session", {"authority": authority,
                             **{key: summary.get(key, "UNKNOWN") for key in session_fields}})
                self.display("Timeline", {"authority": authority, "retained_event_count": len(timeline),
                             "display": "Most recent 200 events; full history remains in the journal/capsule",
                             "events": timeline[-200:]})
                self.display("Git", {"authority": authority, "commits": summary.get("commits", []),
                             "git_state": summary.get("git", "UNKNOWN"),
                             "push_verification": summary.get("push_verification", "UNKNOWN"),
                             "events": [event for event in timeline if any(word in event.get("event_type", "")
                                        for word in ("GIT", "COMMIT", "PUSH"))][-100:],
                             "rule": "Commit creation, push attempt and verified publication are separate facts."})
                self.display("Tests", {"authority": authority, "attempts": summary.get("tests", []),
                             "events": [event for event in timeline if event.get("event_type", "").startswith("TEST_")][-100:],
                             "rule": "TEST EXECUTED != TEST PASSED. Unparsed counts remain UNKNOWN."})
                self.display("Errors", {"authority": authority, "errors": summary.get("errors", []),
                             "events": [event for event in timeline if any(word in event.get("event_type", "")
                                        for word in ("ERROR", "CONTRADICTION", "INVALIDATED"))][-100:],
                             "rule": "Later success does not erase contradictions or earlier failures."})
                if self.live_history is not None and self.live_session is None:
                    self.display("Capsules", {"authority": "HISTORICAL_ONLY", "session": summary,
                                 "safe_to_resume": "UNKNOWN", "mutation_authorized": False})
                self.display("Evidence", {"live_authority": authority, "current_safety": "UNKNOWN",
                             "evidence_grades": ["REPORTED", "OBSERVED", "VERIFIED"],
                             "reconciliation_states": ["SUPPORTED", "CONTRADICTED", "UNKNOWN", "STALE", "INVALIDATED"],
                             "filesystem_exclusivity": "UNKNOWN", "production_mutation": "DISABLED",
                             "assessment": self.model.evidence()})
            self.refresh_live_controls()

        def guarded(self, action):
            try:
                action()
                self.log.append("Operation completed. No repository mutation authority granted.")
            except (ValueError, OSError, RuntimeError):
                self.log.append("Operation refused: invalid, unavailable or existing output.")
                QMessageBox.warning(self, "Operation refused", "Check the input format and choose a new export filename. No repository action was performed.")
            self.refresh()

        def open_file(self):
            path, _ = QFileDialog.getOpenFileName(self, "Open reviewed historical evidence", "", "CGC evidence (*.json *.cgcpack)")
            if path: self.guarded(lambda: self.load_path(path))

        def load_path(self, path):
            if Path(path).suffix.lower() == ".cgcpack":
                try:
                    historical = open_capsule(path)
                except ValueError:
                    pass
                else:
                    if self.active_live():
                        raise ValueError("END_CURRENT_SESSION_BEFORE_LIVE_IMPORT")
                    self.live_session = None
                    self.live_history = historical
                    self.navigation.setCurrentRow(PAGES.index("Timeline"))
                    return
            self.model.load(read_input(path))

        def example(self):
            self.guarded(lambda: self.model.load(sdk.decode(resource("example.json"))))
            self.log.append("SYNTHETIC example loaded; not observed project evidence.")
            self.refresh()

        def export(self, extension, convert):
            if not self.model.status()["snapshot_loaded"]:
                QMessageBox.information(self, "Select evidence", "Open a snapshot or capsule first.")
                return
            path, _ = QFileDialog.getSaveFileName(self, "Export to a new file", "CGC-report." + extension)
            if path: self.guarded(lambda: save_new(path, convert(self.model.snapshot())))

        def export_capsule(self): self.export("cgcpack", sdk.export_capsule)
        def export_report(self): self.export("html", sdk.report)

        def change_mode(self, value):
            self.model.mode = Mode(value)
            self.log.append("Explicit mode selected: " + value + ". Production execution remains disabled.")
            self.refresh()

        def dry_run(self):
            self.display("Recovery Review", DryRunExecutor().execute("CHECKPOINT", self.model.mode))

        def simulate(self):
            self.display("Recovery Review", SimulationExecutor().execute("CHECKPOINT", self.model.mode))

        def closeEvent(self, event):
            self.live_timer.stop()
            if self.live_job is not None:
                self.close_requested = True
                event.ignore()
                return
            if self.active_live() and not self.close_record_attempted:
                self.close_requested = True
                self.close_record_attempted = True
                self.run_live("Record desktop interruption", lambda: self.live_session.interrupt("Desktop closed before end and preserve"))
                event.ignore()
                return
            self.close_requested = True
            event.accept()

    return Window()


def main(mode=Mode.READ_ONLY_SAFE, smoke_output=None):
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(["CGC"])
    app.setApplicationName("CREDID GUARDIAN CODEX")
    app.setApplicationVersion(__version__)
    window = create_window(mode)
    window.show()
    if smoke_output is not None:
        import os
        from PySide6.QtCore import QTimer, QBuffer, QIODevice
        # An explicit packaging smoke may select historical live evidence.
        # Normal desktop startup never reads this variable or opens its path.
        smoke_capsule = os.environ.get("CGC_SMOKE_LIVE_CAPSULE")
        def smoke():
            try:
                if smoke_capsule:
                    window.load_path(smoke_capsule)
                    window.refresh()
                else:
                    window.example()
                for index in range(len(PAGES)):
                    window.navigation.setCurrentRow(index)
                    app.processEvents()
                window.navigation.setCurrentRow(PAGES.index("Live Session") if smoke_capsule else 0)
                app.processEvents()
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                if not window.grab().save(buffer, "PNG"):
                    raise RuntimeError("SCREENSHOT_FAILED")
                save_new(smoke_output, bytes(buffer.data()))
                window.close()
                app.exit(0)
            except (ValueError, OSError, RuntimeError):
                app.exit(2)
        QTimer.singleShot(250, smoke)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
