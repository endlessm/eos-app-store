import uuid
from osapps.shortcuts import Shortcuts

class AppShortcut(object):

    def __init__(self, key, name, icon, params=[], uid=None):
        self._icon = icon
        self._key = key
        self._name = name
        self._params = params
        self._children = Shortcuts()
        self._parent = None
        self._uuid = uid
       
    def __eq__(self, other):
        return self._uuid == other.uuid()

    def __ne__(self, other):
        return not self.__eq__(other)

    def parent(self):
        return self._parent

    def uuid(self):
        return self._uuid

    def set_uuid(self, uid):
        self._uuid = uid
    
    def icon(self):
        return self._icon
    
    def key(self):
        return self._key
    
    def name(self):
        return self._name
    
    def params(self):
        return self._params
    
    def add_child(self, child):
        child._parent = self
        self._children.append(child)
        
    def remove_child(self, child):
        if child in self._children:
            self._children.remove(child)
        child._parent = None
        
    def children(self):
        return self._children
    
    def has_children(self):
        return not self._key or len(self._children) > 0

    def get_child_by_name(self, name):
        name = name.strip()
        for ch in self._children:
            if ch.name() == name:
                return ch
        return None
        
