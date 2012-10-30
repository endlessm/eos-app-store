class ApplicationModel:
    def __init__(self, desktop_file_path, application_id, categories):
        self._desktop_file_path = desktop_file_path
        self._id = application_id
        self._categories = categories
    
    def get_categories(self):
        return self._categories 
    
    def __eq__(self, other):
        return self._id == other._id
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return self._id.__hash__()
    
    def visit(self, visitor):
        for category in self._categories:
            visitor(category, self)
    
    def id(self):
        return self._id