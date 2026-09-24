import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from PySide6.QtWidgets import QApplication
from cgcchild.gui import create_window, PAGES
from cgcchild.execution import Mode


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication(['CGC-test'])

    def test_pages_mode_and_example(self):
        window = create_window()
        window.show()
        self.app.processEvents()
        self.assertEqual(window.stack.count(), 13)
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
        window.close()

    def test_imported_markup_stays_plain(self):
        window = create_window()
        window.display('Logs', '<script>dangerous()</script>')
        self.assertEqual(window.views['Logs'].toPlainText(), '<script>dangerous()</script>')
        window.close()
