from ui.abstract_notifier import AbstractNotifier

class InstallNotifierModel(AbstractNotifier):
    def __init__(self):
        pass
    
    def should_install(self):
        return True
    