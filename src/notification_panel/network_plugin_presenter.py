class NetworkPluginPresenter(object):
    def __init__(self, view, model):
        self._view = view
        self._model = model
    
        self._model.add_state_changed_listener(self.update_network_state)
        
        self.update_network_state()
        
    def update_network_state(self):
        self._model.display_strength_on(self._view.display_network_strength)
        
