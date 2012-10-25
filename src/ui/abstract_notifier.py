class AbstractNotifier():
    def _notify(self, attribute):
        if hasattr(self, attribute):
            method = getattr(self, attribute)
            method()
    
    def add_listener(self, event_type, callback):
        setattr(self, event_type, callback)
