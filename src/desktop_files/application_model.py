from desktop_files.desktop_file_model import DesktopFileModel
import os

class ApplicationModel(DesktopFileModel):
    BROWSER_APP = 'epiphany-browser '

    def __init__(self, model_id, desktop_file_path, categories, name=None, comment=None, icon=None, class_name=None, executable=None):
        super(ApplicationModel, self).__init__(model_id, desktop_file_path, name, comment, icon, class_name)
        self._categories = categories
        self._url = self._remove_prefix(executable, self.BROWSER_APP)

    def get_categories(self):
        return ['All']

    def visit_categories(self, visitor):
        for category in self.get_categories():
            visitor(category, self)

    def install(self):
        if self.class_name():
            class_string = '\nX-EndlessM-Class-Name=' + self.class_name()
        else:
            class_string = ''
            
        with open(self.file_path(), 'w') as f:
            f.write('[Desktop Entry]\nType=Application\nName=' + self.name() + '\nComment=' + self.comment() +
                    '\nIcon=' + self.icon() + class_string + '\n')

    def uninstall(self):
        os.unlink(self.file_path())    

    def _remove_prefix(self, text, prefix):
        return text[len(prefix):] if text.startswith(prefix) else text
