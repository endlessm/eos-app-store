from network_plugin_model import NetworkPluginModel

class NetworkPluginPresenter(object):
    def __init__(self, view, model):
        self._view = view
        self._model = model
    
        self._model.add_listener(NetworkPluginModel.NETWORK_STATE_CHANGED, self._update_network_state)
        
        self._update_network_state()
        
    def _update_network_state(self):
        self._view.display_network_state(self._model.get_network_state())
        
