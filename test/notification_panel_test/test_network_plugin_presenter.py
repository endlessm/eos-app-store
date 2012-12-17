import unittest
from mock import Mock
from notification_panel.network_plugin_presenter import NetworkPluginPresenter
from notification_panel.network_plugin_model import NetworkPluginModel

class NetworkPluginPresenterTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_view = Mock()
        self._mock_model = Mock()
        
        self._mock_model.add_listener = self._mock_model_add_listener
        self._mock_model.get_network_state = Mock(return_value=5678)
        
        self._test_object = NetworkPluginPresenter(self._mock_view, self._mock_model)

    def _mock_model_add_listener(self, name, callback):
        self._model_listener_name = name
        self._model_listener_callback = callback
    
    def test_initially_update_the_view_with_model_state(self):
        self._mock_view.display_network_state.assert_called_once_with(5678)      
    
    def test_update_network_state_updates_the_view(self):
        self._mock_view.display_network_state.reset_mock()
        self._mock_model.get_network_state = Mock(return_value=1234)
        
        self.assertEquals(NetworkPluginModel.NETWORK_STATE_CHANGED, self._model_listener_name)
        self._model_listener_callback()
        
        self._mock_view.display_network_state.assert_called_once_with(1234)      