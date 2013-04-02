import os
import json
from desktop_files.desktop_file_utilities import DesktopFileUtilities

class DesktopModel():
    def get_shortcuts(self, directory):
        files = self._find_desktop_files_in_directory(directory)
        order_list = self._read_order_file_in_directory(directory)
        ordered_model_list = self._build_ordered_list_of_models(files, order_list)
        self.write_order(os.path.join(directory, '.order'), ordered_model_list)
        return ordered_model_list        

    def write_order(self, order_filename, ordered_model_list=[]):
        ordered_id_list = []
        for model in ordered_model_list:
            ordered_id_list.append(model.id())
        json.dump(ordered_id_list, open(order_filename, 'w'))

    def _build_ordered_list_of_models(self, files, order_list):
        ordered_model_list = []
        for item in order_list:
            model = files.get(item, None)
            if model is not None:
                ordered_model_list.append(model)
                del files[item]
                break
        
        for model in files.itervalues():
            ordered_model_list.append(model)
        
        return ordered_model_list

    def _read_order_file_in_directory(self, directory):
        order_list = []
        order_filename = os.path.join(directory, '.order')
        if os.path.isfile(order_filename):
            fp = open(order_filename, 'r')
            order_list = json.load(fp)
        return order_list
        
    def _find_desktop_files_in_directory(self, directory):
        file_model_list = DesktopFileUtilities().get_desktop_file_models(directory)
        files = {}
        for model in file_model_list:
            files[model.id()] = model
        return files
    
        