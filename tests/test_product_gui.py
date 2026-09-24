import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
import time
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication
from cgcchild.gui import create_window, PAGES
from cgcchild.execution import Mode


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication(['CGC-test'])

    def close_window(self, window):
        window.close()
        deadline = time.monotonic() + 15
        while window.live_job is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertIsNone(window.live_job)
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_pages_mode_and_example(self):
        window = create_window()
        window.show()
        self.app.processEvents()
        self.assertEqual(window.stack.count(), 18)
        for index, page in enumerate(PAGES):
            window.navigation.setCurrentRow(index)
            self.assertEqual(window.stack.currentIndex(), index)
            self.assertTrue(window.views[page].toPlainText())
        window.example()
        self.assertIn('SYNTHETIC', window.views['Logs'].toPlainText())
        window.simulate()
        self.assertIn('REFUSED', window.views['Recovery Review'].toPlainText())
        window.mode_box.setCurrentText(Mode.SIMULATION.value)
        window.simulate()
        self.assertIn('SIMULATED', window.views['Recovery Review'].toPlainText())
        self.assertIn('DISABLED', window.banner.text())
        self.close_window(window)

    def test_imported_markup_stays_plain(self):
        window = create_window()
        window.display('Logs', '<script>dangerous()</script>')
        self.assertEqual(window.views['Logs'].toPlainText(), '<script>dangerous()</script>')
        self.close_window(window)
