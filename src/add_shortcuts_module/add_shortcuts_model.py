import os
from shortcut_category import ShortcutCategory

class AddShortcutsModel():
    def __init__(self):
        self._DEFAULT_ICON_PATH = '/usr/share/endlessm/icons/folders'

    def get_category_data(self):
        data = []
        section_app = ShortcutCategory(_('APP'), True)
#        section_app.subcategories = [ShortcutCategory(_('POPULAR')),
#                                     ShortcutCategory(_('PRODUCTIVITY')),
#                                     ShortcutCategory(_('ENTERTAINMENT')),
#                                     ShortcutCategory(_('GAMES')),
#                                     ShortcutCategory(_('HEALTH')),
#                                     ShortcutCategory(_('WORK')),
#                                     ShortcutCategory(_('SOCIAL')),
#                                     ShortcutCategory(_('MY TOWN'))]
        section_web = ShortcutCategory(_('WEB'))
        section_folder = ShortcutCategory(_('FOLDER'))

        data.append(section_app)
        data.append(section_web)
        data.append(section_folder)
        return data

    def create_directory(self, folder_name, path=''):
        if not path:
            path = '~/'
        full_path = path + folder_name
        return full_path
        #if not os.path.exists(full_path):
        #    try:
        #        os.makedirs(full_path)
        #        return full_path
        #    except:
        #        print 'ERROR occurred while trying to make directory', full_path
        #        return ''

    def get_folder_icons(self, path, prefix='', suffix=''):
        if not path:
            path = self._DEFAULT_ICON_PATH

        icon_list = self.get_icon_list(path)
        icons = []
        
        for icon in icon_list:
            if icon.startswith(prefix) and (icon.endswith(suffix + '.png') or icon.endswith(suffix + '.svg')):
                if not os.path.islink(os.path.join(path, icon)):
                    icons.append(icon)
                    
        return icons

    def get_icon_list(self, path):
        return os.listdir(path)
