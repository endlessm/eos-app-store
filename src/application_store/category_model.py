
class CategoryModel:
    def __init__(self, name):
        self._name = name
        self._applications = set()
    
    def name(self):
        return self._name
    
    def add_application(self, application):
        self._applications.add(application)

    def get_applications_set(self):
        return frozenset(self._applications)

    def __eq__(self, other):
        return self._name == other._name
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return self._name.__hash__()