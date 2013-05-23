import json
from app_shortcut import AppShortcut
import os
import shutil
import uuid
from shortcuts import Shortcuts

from eos_log import log
from eos_util.locale_util import LocaleUtil


class DesktopLocaleDatastore(object):
    DEFAULT_DESKTOP_SHORTCUTS_FILE = os.path.expanduser("~/.endlessm/desktop.json")
    DEFAULT_DIRECTORY="/etc/endlessm/"
    PREFIX = "desktop."

    def __init__(self, desktop_file=DEFAULT_DESKTOP_SHORTCUTS_FILE, directory=DEFAULT_DIRECTORY, locale_utils=LocaleUtil()):
        self._dir = directory
        self._desktop_file = desktop_file
        self._locale_utils = locale_utils

        self._store_uuid = False


    def get_all_shortcuts(self):
        shortcuts = Shortcuts()
        try:

            with open(self._get_filename(), "r") as f:
                for value in json.load(f):
                    shortcut = self._convert_dict_to_shortcut(value)
                    shortcuts.append(shortcut)

            #TODO: (kyle and matt i) REFACTOR: this guarantees uuids are stored for each id before first use
            if not self._store_uuid:
                self._store_uuid = True
                self.set_all_shortcuts(shortcuts)

        except Exception as e:
            log.error("An error occurred trying to read the file: " + self._get_filename(), e)

        return shortcuts


    def _get_filename(self):
        if not os.path.exists(self._desktop_file):
            lang_code = self._locale_utils.get_locale()
            filename = self._find_localized_desktop_file(lang_code)
            shutil.copyfile(filename, self._desktop_file)

        return self._desktop_file

    def set_all_shortcuts(self, shortcuts):

        try:
            with open(self._get_filename(), "w") as f:
                json.dump([self._convert_shortcut_to_dict(sc) for sc in shortcuts], f)
        except Exception as e:
            log.error("An error occurred trying to open the file: " + self._get_filename(), e)

    def _find_localized_desktop_file(self, lang_code):
        filename = os.path.join(self._dir, self.PREFIX + lang_code)
        if not os.path.exists(filename):
            log.error("Could not read the localized desktop file: " + filename)
            log.error("Reading default desktop file...")
            return os.path.join(self._dir, self.PREFIX + self._locale_utils.get_default_locale())
        return filename


    def _convert_dict_to_shortcut(self, dictionary):
        icon = dictionary.get("icon")
        key = dictionary.get("key")
        name = dictionary.get("name")
        params = dictionary.get("params", [])

        children = dictionary.get("children", [])

        _uuid = dictionary.get("uuid")

        shortcut = AppShortcut(key, name, icon, params, _uuid)

        for child in children:
            shortcut.add_child(self._convert_dict_to_shortcut(child));

        return shortcut

    def _convert_shortcut_to_dict(self, shortcut):
        shortcut_dict = {}

        shortcut_dict["icon"] = shortcut.icon()
        shortcut_dict["key"] = shortcut.key()
        shortcut_dict["name"] = shortcut.name()
        shortcut_dict["uuid"] = shortcut.uuid()
        if shortcut.params():
            shortcut_dict["params"] = shortcut.params()

        if shortcut.children():
            children = []
            for child in shortcut.children():
                children.append(self._convert_shortcut_to_dict(child))

            shortcut_dict["children"] = children

        return shortcut_dict

    def add_shortcut(self, shortcut):
        shortcuts = self.get_all_shortcuts()
        shortcuts.append(shortcut)
        self.set_all_shortcuts(shortcuts)

