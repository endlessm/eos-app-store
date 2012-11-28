import unittest
from mock import Mock
from notification_panel.battery_view import BatteryView
from notification_panel.panel_constants import PanelConstants

class BatteryViewTestCase(unittest.TestCase):
    def setUp(self):
        self.mock_parent = Mock()
        self.mock_parent.connect = Mock()
        self.mock_parent.set_visible_window = Mock()
        self.mock_parent.set_size_request = Mock()
        self.mock_parent.queue_draw = Mock()
        self.test_object = BatteryView(self.mock_parent, 1)
    
    def test_expose_event_is_attached_once(self):
        self.mock_parent.connect.assert_called_once_with("expose-event", self.test_object._draw)
    
    def test_display_battery_sets_values(self):
        level = 10
        time_to_depletion = 1200
        charging = True
        
        self.test_object._recalculate_battery_bounds = Mock()
        
        self.test_object.display_battery(level, time_to_depletion, charging)
        
        self.assertEqual(level, self.test_object._level)
        self.assertEqual(time_to_depletion, self.test_object._time_to_depletion)
        self.assertEqual(charging, self.test_object._charging)
        self.mock_parent.set_visible_window.assert_called_once_with(False)
        self.mock_parent.set_size_request.assert_called_once_with(PanelConstants.get_icon_size() + 2 * self.test_object.HORIZONTAL_MARGIN, PanelConstants.get_icon_size())
        self.mock_parent.queue_draw.assert_called_once_with()
    
