import os
import json
from EosAppStore.eos_log import log
from gi.repository import GLib
from gi.repository import Gio

class InstalledApplicationsModel():
    EOS_SHELL_SCHEMA = 'org.gnome.shell'
    ICON_GRID_LAYOUT_SETTING = 'icon-grid-layout'
    USER_DESKTOP_DIRECTORY_HOME = \
        os.path.expanduser('~/.local/share/desktop-directories')

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
        # Include eos-app-store as an installed application
        self._installed_applications.append("eos-app-store.desktop")

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

    def create_folder(self, folder_name, icon_name):
        self._load_data()
        index = 0
        directory_name = self._directory_name(index)
        # Check in sequence for a unique .directory file name not in use
        while self.is_installed(directory_name):
            index += 1
            directory_name = self._directory_name(index)
        self._generate_directory_file(directory_name, folder_name, icon_name)
        value = self._settings.get_value(self.ICON_GRID_LAYOUT_SETTING)
        layout = value.unpack()
        entries = layout[""]
        entries.append(directory_name)
        layout[""] = entries
        layout[directory_name] = []
        self._settings.set_value(self.ICON_GRID_LAYOUT_SETTING, GLib.Variant("a{sas}", layout))
        self._settings.sync()

    def _directory_name(self, index):
        return 'eos-folder-user-' + str(index) + '.directory'

    def _generate_directory_file(self, directory_name, folder_name, icon_name):
        if not os.path.exists(self.USER_DESKTOP_DIRECTORY_HOME):
            os.makedirs(self.USER_DESKTOP_DIRECTORY_HOME)
        directory_path = os.path.join(self.USER_DESKTOP_DIRECTORY_HOME,
                                      directory_name)
        f = open(directory_path, 'w')
        f.write('[Desktop Entry]\n')
        f.write('Version=1.0\n')
        f.write('Name=' + folder_name + '\n')
        f.write('Type=Directory\n')
        f.write('Icon=' + icon_name + '\n')
        f.close()
