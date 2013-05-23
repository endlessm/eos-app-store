from EosAppStore.desktop_files.desktop_file_model import DesktopFileModel
import os

class FolderModel(DesktopFileModel):
    
    BASEPATH = os.environ["XDG_DATA_DIRS"].split(":")[0] if os.environ["XDG_DATA_DIRS"] else "/usr/share"
    FOLDER_ICON_PATH = BASEPATH + '/icons/EndlessOS/64x64/folders'
    
    def __init__(self, model_id, desktop_file_path, name=None, comment=None, icon=None, class_name=None):
        super(FolderModel, self).__init__(model_id, desktop_file_path, name, comment, icon, class_name,
                                          icon_path=self.FOLDER_ICON_PATH)

    def install(self):
        os.mkdir(self.file_path())
        
        if self.class_name():
            class_string = '\nX-EndlessM-Class-Name=' + self.class_name()
        else:
            class_string = ''
            
        with open(os.path.join(self.file_path(), '.directory'), 'w') as f: 
            f.write('[Desktop Entry]\nType=Directory\nName=' + self.name() + '\nComment=' + self.comment() +
                    '\nIcon=' + self.icon() + class_string + '\n')
    
    def uninstall(self):
        os.unlink(os.path.join(self.file_path(), '.directory'))
        os.rmdir(self.file_path())
