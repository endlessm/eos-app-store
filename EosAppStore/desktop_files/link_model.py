from EosAppStore.desktop_files.desktop_file_model import DesktopFileModel
import os

class LinkModel(DesktopFileModel):
    def __init__(self, file_path, name, url, comment='', icon=None, class_name=None):
        super(LinkModel, self).__init__(url, file_path, name, comment, icon, class_name)
        self._url = url
    
    def url(self):
        return self._url

    def install(self):
        if self.class_name():
            class_string = '\nX-EndlessM-Class-Name=' + self.class_name()
        else:
            class_string = ''
            
        with open(self.file_path(), 'w') as f: 
            f.write('[Desktop Entry]\nType=Link\nName=' + self.name() + '\nURL=' + self.url() +
                    '\nComment=' + self.comment() + '\nIcon=' + self.icon() + class_string + '\n')

    def uninstall(self):
        os.unlink(self.file_path())    
