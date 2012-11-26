from application_store.desktop_file_utilities import DesktopFileUtilities
import os
import json

class DesktopModel():
    def __init__(self):
        pass
    
    def get_shortcuts(self, directory):
        if not os.path.isfile(os.path.join(directory, '.order')):
            self.write_order(directory)
            
        file_model_list = DesktopFileUtilities().get_desktop_file_models(directory)
        return file_model_list        
        
    def write_order(self, directory, ordered_model_list=[]):
        ordered_id_list = []
        for model in ordered_model_list:
            ordered_id_list.append(model.id())
        json.dump(ordered_id_list, open(os.path.join(directory, '.order'), 'w'))
        