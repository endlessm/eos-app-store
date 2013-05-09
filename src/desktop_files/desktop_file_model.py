import os

class DesktopFileModel(object):
    
    APP_ICON_PATH = '/home/endlessm/gnome/source/eos-app-store/usr/share/endlessm/icons/apps'
    MINI_ICON_PATH = '/home/endlessm/gnome/source/eos-app-store/usr/share/endlessm/icons/mini'
    NORMAL_EXT = '_normal.png'
    DOWN_EXT = '_down.png'
    HOVER_EXT = '_hover.png'
    
    def __init__(self, id, file_path, name=None, comment=None, icon=None, class_name=None,
                 icon_path=APP_ICON_PATH, mini_icon_path=MINI_ICON_PATH):
        self._id = id
        self._file_path = file_path
        self._name = name
        self._comment = comment
        self._icon = icon
        self._class_name = class_name
        self._icon_path = icon_path
        self._mini_icon_path = mini_icon_path

    def __eq__(self, other):
        return self._id == other._id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self._id.__hash__()

    def id(self):
        return self._id

    def file_path(self):
        return self._file_path

    def set_file_path(self, new_file_path):
        self._file_path = new_file_path

    def name(self):
        return self._name

    def comment(self):
        return self._comment

    def icon(self):
        return self._icon

    def class_name(self):
        return self._class_name

    def normal_icon(self):
        if self._icon:
            path = os.path.join(self._icon_path, self._icon + self.NORMAL_EXT)
        else:
            path = ''
        return path

    def down_icon(self):
        if self._icon:
            path = os.path.join(self._icon_path, self._icon + self.DOWN_EXT)
        else:
            path = ''
        return path

    def hover_icon(self):
        if self._icon:
            path = os.path.join(self._icon_path, self._icon + self.HOVER_EXT)
        else:
            path = ''
        return path
    
    def mini_icon(self):
        if self._icon:
            path = os.path.join(self._mini_icon_path, self._icon + self.NORMAL_EXT)
        else:
            path = ''
        return path

    def visit_categories(self, visitor):
        pass
