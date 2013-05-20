import os
import json
from eos_log import log
from gi.repository import GLib
from gi.repository import Gio

class InstalledApplicationsModel():
    EOS_SHELL_SCHEMA = 'org.gnome.shell'
    ICON_GRID_LAYOUT_SETTING = 'icon-grid-layout'

    def __init__(self, filename = 'installed_applications.json'):
        self._installed_applications = []
        self._filename = filename
        self._full_path = os.path.join(os.path.expanduser("~/.endlessm"), self._filename)
        self._settings = Gio.Settings.new(schema_id = self.EOS_SHELL_SCHEMA)

    def set_data_dir(self, file_location):
        self._full_path = os.path.join(file_location, self._filename)

    def _load_data(self):
        value = self._settings.get_value(self.ICON_GRID_LAYOUT_SETTING)
        layout = value.unpack()
        self._installed_applications = [item for sublist in layout.values() for item in sublist]

    def installed_applications(self):
        self._load_data()
        return self._installed_applications

    def install(self, application):
        value = self._settings.get_value(self.ICON_GRID_LAYOUT_SETTING)
        layout = value.unpack()
        entries = layout[""]
        entries.append(application)
        layout[""] = entries
        self._settings.set_value(self.ICON_GRID_LAYOUT_SETTING, GLib.Variant("a{sas}", layout))
        self._settings.sync()

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
