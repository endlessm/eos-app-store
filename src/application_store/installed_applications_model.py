import os
import json
from eos_log import log

class InstalledApplicationsModel():
    def __init__(self, filename = 'installed_applications.json'):
        self._installed_applications = []
        self._filename = filename
        self._full_path = os.path.join(os.path.expanduser("~/.endlessm"), self._filename)

    def set_data_dir(self, file_location):
        self._full_path = os.path.join(file_location, self._filename)

    def _load_data(self):
        if os.path.isfile(self._full_path):
            with open(self._full_path, 'r') as fp:
               json_data = json.load(fp)
               if json_data is not None:
                   self._installed_applications = json_data

    def installed_applications(self):
        self._load_data()
        return self._installed_applications

    def install(self, application):
        self._load_data()
        self.install_at(application, len(self._installed_applications))

    def uninstall(self, application):
        self._load_data()
        log.info("removing: " + application)
        log.info("from: " + repr(self._installed_applications))
        self._installed_applications.remove(application)
        with open(self._full_path, "w") as f:
            json.dump(self._installed_applications, f)

    def is_installed(self, application):
        self._load_data()
        return application in self._installed_applications

    def install_at(self, application, index):
        self._load_data()
        self._installed_applications.insert(index, application)
        # TODO Actually install the application on issue 434
        with open(self._full_path, "w") as f:
            json.dump(self._installed_applications, f)
