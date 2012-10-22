import unittest
from mock import Mock

from notification_panel.battery_presenter import BatteryPresenter

class BatteryPresenterTestCase(unittest.TestCase):
    
    def setUp(self):
        self._model = Mock()
        self._view = Mock()
        self._gobj = Mock()
        self._model.time_to_depletion = Mock(return_value=100)
        self._model.level = Mock(return_value=10)
        
        self._test_object = BatteryPresenter(self._view, self._model, self._gobj)
        
        
    def test_constructor_stores_state(self):
        self.assertEquals(self._model, self._test_object._model) 
        self.assertEquals(self._view, self._test_object._view) 

    def test_post_init(self):
        self._view.add_listener = Mock()
        self._view.display_battery = Mock()
        self._test_object._start_poll_battery = Mock()
        
        self._model.charging = Mock(return_value=False)
        
        self._test_object.post_init()
        
        self._view.add_listener.assert_called_once()
        self._view.display_battery.assert_called_once_with(10, 100, False)
        self._test_object._start_poll_battery.assert_called_once_with()

    def test_start_polling(self):
        self._gobj.timeout_add = Mock()
        self._test_object._start_poll_battery()
        self._gobj.timeout_add.assert_called_once_with(BatteryPresenter.REFRESH_TIME, self._test_object._poll_for_battery)
    
    def test_open_settings(self):
        self._view.hide_window = Mock()
        self._model.open_settings = Mock()
        
        self._test_object._open_settings()
        
        self._view.hide_window.assert_called_once_with()
        self._model.open_settings.assert_called_once_with()
        
    def test_display_menu(self):
        self._view.display_menu = Mock()
        
        self._test_object.display_menu()
        
        self._view.display_menu.assert_called_once_with(10, 100)
        
        