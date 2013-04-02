import unittest

from notification_panel.printer_plugin import PrinterSettingsPlugin

class PrinterSettingsPluginTestCase(unittest.TestCase):
    def test_start_command_is_correct(self):
        self.assertEqual('system-config-printer --class=eos-printers', PrinterSettingsPlugin(1).get_launch_command())
