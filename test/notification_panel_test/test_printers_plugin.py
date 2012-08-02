import unittest
from mock import Mock

from notification_panel.printer_plugin import PrinterSettingsPlugin

class PrinterSettingsPluginTestCase(unittest.TestCase):
    def test_start_command_is_correct(self):
        self.assertEqual('gnome-control-center --class=eos-printers printers', PrinterSettingsPlugin.get_launch_command())

