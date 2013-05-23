
class RenameWidgetModel():
    def __init__(self, caller):
        self._caller = caller

    def save(self, new_name):
        self._caller.rename_shortcut(new_name)

    def get_original_name(self):
        return self._caller._identifier
