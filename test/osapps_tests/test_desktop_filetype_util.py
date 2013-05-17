import unittest
from osapps.desktop_filetype_util import DesktopFiletypeUtil

class TestDesktopFiletypeUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = DesktopFiletypeUtil()
        
    def test_get_executable_returns_correct_information(self):
        executable = self._test_object.get_executable("gnome-terminal.desktop")
        self.assertEqual("gnome-terminal", executable)

    def test_get_executable_ignores_special_parameters(self):
        executable = self._test_object.get_executable("libreoffice-calc.desktop")
        self.assertEqual("libreoffice --calc", executable)
        
    def test_get_display_name_returns_correct_information(self):
        name = self._test_object.get_display_name("libreoffice-writer.desktop")
        self.assertEqual("Word Processor", name)
        
