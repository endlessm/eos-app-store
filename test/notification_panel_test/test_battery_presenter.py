import unittest
from mock import Mock

from notification_panel.battery_presenter import BatteryPresenter
from notification_panel.battery_view import BatteryView
from notification_panel.battery_model import BatteryModel
from ui.abstract_notifier import AbstractNotifier

class BatteryPresenterTestCase(unittest.TestCase):
    def setUp(self):
        self._model = Mock()
        self._model.add_listener = self._mock_model_add_listener
         
        self._view = Mock()
        self._view.add_listener = self._mock_view_add_listener
        
        self._gobj = Mock()
        self._model.time_to_depletion = Mock(return_value=100)
        self._model.level = Mock(return_value=10)
        
        self._test_object = BatteryPresenter(self._view, self._model, self._gobj)
        self._test_object.post_init()
        
    def _mock_view_add_listener(self, name, callback):
        self._view_listener_name = name
        self._view_listener_callback = callback
        

    def _mock_model_add_listener(self, name, callback):
        self._model_listener_name = name
        self._model_listener_callback = callback
        
    def test_post_init(self):
        self._view.add_listener = Mock()
        self._view.display_battery = Mock()
        self._model.add_listener = Mock()
        
        self._model.charging = Mock(return_value=True)
        
        self._test_object.post_init()
        
        self.assertEquals(BatteryView.POWER_SETTINGS, self._view_listener_name)
        self.assertEquals(BatteryModel.BATTERY_STATE_CHANGED, self._model_listener_name)
        self._view.display_battery.assert_called_once_with(10, 100, True)

    def test_power_setting_signal_opens_settings(self):
        self._view.hide_window = Mock()
        self._model.open_settings = Mock()
        
        self._view_listener_callback()
        
        self._view.hide_window.assert_called_once_with()
        self._model.open_settings.assert_called_once_with()
        
    def test_update_battery_state_updates_the_view(self):
        self._view.display_battery.reset_mock()
        self._model.charging = Mock(return_value=False)
        
        self._model_listener_callback()
        
        self._view.display_battery.assert_called_once_with(10, 100, False)      
        
    def test_display_menu(self):
        self._view.display_menu = Mock()
        
        self._test_object.display_menu()
        
        self._view.display_menu.assert_called_once_with(10, 100)
    