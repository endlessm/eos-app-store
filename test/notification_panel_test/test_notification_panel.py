import unittest
from mock import Mock
from notification_panel.notification_panel import NotificationPanel

class NotificationPanelTestCase(unittest.TestCase):

    def test_constructor_catches_exception_raised_registering_plugins(self):
        NotificationPanel._register_plugin = Mock(side_effect = Exception('mock register plugin exception'))
        mock_parent = Mock()
        
        try:
            NotificationPanel(mock_parent)
        except Exception, e:
            self.fail('Exception not caught within constructor: ' + e.message)
