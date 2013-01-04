class NetworkPluginPresenter(object):
    def __init__(self, view, model):
        self._view = view
        self._model = model
    
        self._model.add_state_changed_listener(self.update_network_state)
        
        self._model.retrieve_state()
        
    def update_network_state(self, state):
        self._view.display_network_state(state)
       
