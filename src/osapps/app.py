class App(object):
    def __init__(self, app_id, display_name, app_name, app_exec, app_icon, is_whitelisted=False, is_default=False, is_visible=True, children_ids=[]):
        self._app_id = app_id
        self._display_name = display_name
        self._app_name = app_name
        self._app_exec = app_exec
        self._app_icon = app_icon
        self._is_whitelisted = is_whitelisted
        self._is_default = is_default
        self._is_visible = is_visible
        self._children_ids = children_ids
        self._child_apps = []
        
    def id(self):
        return self._app_id
    
    def app_name(self):
        return self._app_name
    
    def display_name(self):
        return self._display_name

    def executable(self):
        return self._app_exec
    
    def icon(self):
        return self._app_icon
    
    def is_whitelisted(self):
        return self._is_whitelisted
    
    def is_default(self):
        return self._is_default

    def is_visible(self):
        return self._is_visible
    
    def get_children_ids(self):
        return self._children_ids
    
    def has_children(self):
        return len(self._children_ids) > 0
    
    def get_children(self):
        return self._child_apps
    
    def add_child(self, child_app):
        self._child_apps.append(child_app)
    
    def rename(self, new_name):
        self._display_name = new_name

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self._app_id == other._app_id)

    def __ne__(self, other):
        return not self.__eq__(other)
