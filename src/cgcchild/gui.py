"""Local desktop consumer. Imported text is always rendered as plain text."""
import json
import platform
import sys
from . import __version__, sdk
from .core import Workbench, read_input, save_new, security_debt, resource
from .execution import Mode, DryRunExecutor, SimulationExecutor

PAGES = ("Dashboard", "Project Status", "Evidence", "Continuity", "Safe Resume",
         "Reports", "Capsules", "Recovery Review", "Plugin / SDK Status",
         "Security Debt", "System Information", "Logs", "About")


def create_window(mode=Mode.READ_ONLY_SAFE):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
        QListWidget, QStackedWidget, QPlainTextEdit, QPushButton, QFileDialog, QMessageBox, QComboBox)

    class Window(QMainWindow):
        def __init__(self):
            super().__init__()
            self.model = Workbench(mode)
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

        def display(self, page, value):
            self.views[page].setPlainText(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True))

        def refresh(self):
            status = self.model.status()
            self.banner.setText("EXPERIMENTAL  |  " + self.model.mode.value + "  |  Current safety: UNKNOWN  |  Production mutation: DISABLED")
            self.display("Dashboard", "THE GUARDIAN OBSERVES. CODEX PRESERVES.\n\n"
                         + ("Historical snapshot loaded. Review its uncertainty before acting." if status["snapshot_loaded"] else "Open a reviewed JSON snapshot or .cgcpack to begin.\nThe synthetic example is available for an offline tour.")
                         + "\n\nNo quota account, repository or remote is polled.\nExports contain historical evidence, never execution authority.")
            self.display("Project Status", status)
            self.display("Evidence", self.model.evidence())
            self.display("Security Debt", security_debt())
            self.display("System Information", {"system": platform.system(), "release": platform.release(),
                         "python": platform.python_version(), "product_version": __version__, "network_listener": False})
            self.display("Plugin / SDK Status", {"plugin": "DISTRIBUTABLE / NOT AUTO-INSTALLED",
                         "python_sdk": sdk.negotiate(sdk.API_VERSION), "node_sdk": "Bundled separately in sdk/javascript",
                         "host_interoperability": "NOT_ACCEPTED", "local_service": "Foreground MCP stdio; explicit input required"})
            self.display("Reports", "Export an inert HTML report using the toolbar.\nReports retain historical labels and UNKNOWN safety.\nAn existing file is never overwritten.")
            self.display("Capsules", "Open / export .cgcpack using the toolbar.\nArchives are validated in memory; no archive member is extracted.\nSource files, Git objects and current authority are not included.")
            self.display("About", "CREDID GUARDIAN CODEX\nCGCCHILD " + __version__ + " — experimental Windows release\n\nApache-2.0\nOriginal author: Mihai-Bogdan Simion\n\nONE SENSOR. MULTIPLE CONSUMERS.\n\nQt / PySide6 is dynamically bundled; see THIRD_PARTY_NOTICES.md and licenses in the portable package.")
            if status["snapshot_loaded"]:
                self.display("Continuity", status["summary"])
                self.display("Safe Resume", self.model.review())
                self.display("Recovery Review", self.model.review())
            else:
                for page in ("Continuity", "Safe Resume", "Recovery Review"):
                    self.display(page, "No snapshot selected. Current safety remains UNKNOWN.")
            self.display("Logs", "\n".join(self.log[-100:]))

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
            if path: self.guarded(lambda: self.model.load(read_input(path)))

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

    return Window()


def main(mode=Mode.READ_ONLY_SAFE, smoke_output=None):
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(["CGC"])
    app.setApplicationName("CREDID GUARDIAN CODEX")
    app.setApplicationVersion(__version__)
    window = create_window(mode)
    window.show()
    if smoke_output is not None:
        from PySide6.QtCore import QTimer, QBuffer, QIODevice
        def smoke():
            try:
                window.example()
                for index in range(len(PAGES)):
                    window.navigation.setCurrentRow(index)
                    app.processEvents()
                window.navigation.setCurrentRow(0)
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
