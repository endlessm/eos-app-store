import os
from xdg.DesktopEntry import DesktopEntry
from desktop_files.application_model import ApplicationModel
from desktop_files.link_model import LinkModel
from desktop_files.folder_model import FolderModel


class DesktopFileUtilities:
    def get_desktop_files_and_folders(self, the_dir):
        return self._walk_dir(the_dir, lambda f, d: f.endswith(".desktop") or os.path.isdir(os.path.join(d,f)))
    
    def get_desktop_files(self, the_dir):
        return self._walk_dir(the_dir, lambda f, d: f.endswith(".desktop"))

    def _walk_dir(self, the_dir, inclusion_test):
        desktop_files = []
        for filename in os.listdir(the_dir):
            if inclusion_test(filename, the_dir):
                desktop_files.append(filename)
        return desktop_files

    def create_model(self, file_path, model_id):
        desktop_entry = self._get_desktop_entry(file_path)
        
        name = desktop_entry.getName()
        comment = desktop_entry.getComment()
        icon = desktop_entry.getIcon()
        class_name = self._get_class_name(desktop_entry)
        if desktop_entry.getType() == 'Application':
            categories = desktop_entry.getCategories()
            return ApplicationModel(model_id, file_path, categories, name, comment, icon, class_name)
        elif desktop_entry.getType() == 'Link':
            url = desktop_entry.getURL()
            return LinkModel(file_path, name, url, comment, icon, class_name)
        elif desktop_entry.getType() == 'Directory' or os.path.isdir(file_path):
            if name == '' :
                name = model_id
            return FolderModel(model_id, file_path, name, comment, icon, class_name)
        
    def _get_desktop_entry(self, file_path):
        desktop_entry = DesktopEntry()
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, ".directory")
        if os.path.isfile(file_path):
            desktop_entry.parse(file_path)
        return desktop_entry

    def get_desktop_file_models(self, the_dir):
        desktop_file_models = []
        desktop_files = self.get_desktop_files_and_folders(the_dir)
        for desktop_file in desktop_files:
            # Note: this method uses the file name as the name of the model
            desktop_file_models.append(self.create_model(os.path.join(the_dir, desktop_file), desktop_file))
        return desktop_file_models
    
    def _get_class_name(self, desktop_entry):
        # Return the custom class name field if provided
        # Otherwise, return the base name of the exec string
        class_name = desktop_entry.get('X-EndlessM-Class-Name')
        if not class_name:
            exec_string = desktop_entry.get('Exec')
            if exec_string:
                class_name = os.path.basename(exec_string.split()[0])
        return class_name
