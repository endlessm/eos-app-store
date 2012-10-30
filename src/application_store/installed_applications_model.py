from sets import ImmutableSet
import os
import json
from fileinput import close

class InstalledApplicationsModel():
    def __init__(self, file_location=''):
        self._installed_applications = []
        self.set_data_dir(file_location)
    
    def set_data_dir(self, file_location):
        self._file_location = file_location
        self._full_path = os.path.join(self._file_location, 'installed_applications.json')
        if os.path.isfile(self._full_path):
            fp = open(self._full_path, 'r')
            json_data = json.load(fp)
            if json_data:
                self._installed_applications = json_data['installed_applications']

    
    def installed_applications(self):
        return self._installed_applications
    
    def install(self, application):
        self._installed_applications.append(application)
        json.dump(self._installed_applications, open(self._full_path, "w"))
    
    def uninstall(self, application):
        self._installed_applications.remove(application)
        json.dump(self._installed_applications, open(self._full_path, "w"))
        
    def is_installed(self, application):
        return False