import gtk
import os

class AddShortcutsModel():
    def get_tree_data(self):
        data = gtk.TreeStore(str)
        section = data.append(None, ['APP'])
        data.append(section, ['POPULAR'])
        data.append(section, ['PRODUCTIVITY'])
        data.append(section, ['ENTERTAINMENT'])
        data.append(section, ['GAMES'])
        data.append(section, ['HEALTH'])
        data.append(section, ['WORK'])
        data.append(section, ['SOCIAL'])
        data.append(section, ['MY TOWN'])
        data.append(None, ['WEBSITE'])
        data.append(None, ['FOLDER'])
        return data
    
    def create_directory(self, folder_name, path=''):
        if not path:
            path = '/home/rew/'
        full_path = path + folder_name
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
                return full_path
            except:
                print 'ERROR occured while trying to make directory', full_path
                return ''