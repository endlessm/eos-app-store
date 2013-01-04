import unittest
from mock import Mock
from notification_panel.network_plugin_presenter import NetworkPluginPresenter

class NetworkPluginPresenterTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_view = Mock()
        self._mock_model = Mock()
        
        self._test_object = NetworkPluginPresenter(self._mock_view, self._mock_model)

    def test_register_listener_for_state_change_on_init(self):
        self._mock_model.add_state_changed_listener.assert_called_once_with(self._test_object.update_network_state)
        
    def test_initially_update_the_view_with_model_state(self):
        self._mock_model.retrieve_state.assert_called_once_with()
    
    def test_update_network_state(self):
        mock_state = Mock()
        
        self._test_object.update_network_state(mock_state)
        
        self._mock_view.display_network_state.assert_called_once_with(mock_state)
