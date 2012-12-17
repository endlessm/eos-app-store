import unittest
from mock import Mock
from notification_panel.network_plugin_model import NetworkPluginModel

class NetworkPluginModelTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_network_util = Mock()
        self._mock_logger = Mock()
        
        self._test_object = NetworkPluginModel(self._mock_network_util)

    def test_initially_register_device_changed_callback_that_registers_callback_for_ap_strength_and_notifies_state_listeners(self):
        internal_callback = self._test_object._network_state_changed
        
        self._mock_network_util.register_device_change_listener.assert_called_once_with(internal_callback)
        self._mock_network_util.reset_mock()
        
        callback = Mock()
        self._test_object.add_listener(NetworkPluginModel.NETWORK_STATE_CHANGED, callback)

        internal_callback()
        
        self._mock_network_util.register_ap_callback.assert_called_once_with(self._test_object._network_strength_changed)
        self.assertTrue(callback.called)
        
    def test_initially_register_ap_strength_changed_callback_that_notifies_listeners_of_state_change(self):
        internal_callback = self._test_object._network_strength_changed
        
        self._mock_network_util.register_ap_callback.assert_called_once_with(internal_callback)
        
        callback = Mock()
        self._test_object.add_listener(NetworkPluginModel.NETWORK_STATE_CHANGED, callback)
        
        internal_callback()
        
        self.assertTrue(callback.called)
        
    def test_get_network_strength_returns_network_util_values(self):
        mock_value = 10
        self._mock_network_util.get_network_state = Mock(return_value=mock_value)
        
        self.assertEqual(mock_value, self._test_object.get_network_state())
        
    def test_if_we_get_an_exception_trying_to_get_wifi_strength_return_none(self):
        self._mock_network_util.get_network_state = Mock(side_effect = Exception())
         
        actual_strength = self._test_object.get_network_state()
     
        self.assertEqual(None, actual_strength)
        
    def test_if_we_get_an_exception_trying_to_register_device_listener_dont_die_and_log_error(self):
        self._mock_network_util.register_device_change_listener = Mock(side_effect = Exception())
        
        try:
            self._test_object = NetworkPluginModel(self._mock_network_util)
        except:
            self.fail("Should not have thrown exception")

        
    def test_if_we_get_an_exception_trying_to_register_network_strength_listener_dont_die_and_log_error(self):
        self._mock_network_util.register_ap_callback = Mock(side_effect = Exception())
        
        try:
            self._test_object = NetworkPluginModel(self._mock_network_util)
        except:
            self.fail("Should not have thrown exception")
