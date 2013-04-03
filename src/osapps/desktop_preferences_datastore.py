import json
import os
from osapps.os_util import OsUtil
from eos_log import log
from eos_util.image import Image

class DesktopPreferencesDatastore(object):
    PREF_DIRNAME = os.path.expanduser('~/.endlessm')
    PREF_FILENAME = os.path.join(PREF_DIRNAME, 'desktop_preferences.json')
    DEFAULT_BG_LOCATION = '/usr/share/backgrounds/default_background.png'
    PREF_BG_KEY = 'background'

    _instance = None

    def __init__(self, os_util):
        try:
            os.makedirs(self.PREF_DIRNAME)
        except:
            pass

        self._preferences = dict()
        self._preferences_file = os.path.join(self.PREF_DIRNAME, self.PREF_FILENAME)
        self._os_util = os_util

        self._background_image = None
        self._scaled_image = None
        self._scaled_width = None
        self._scaled_height = None

    @staticmethod
    def get_instance(os_util=OsUtil()):
        if DesktopPreferencesDatastore._instance == None:
            DesktopPreferencesDatastore._instance = DesktopPreferencesDatastore(os_util)

        return DesktopPreferencesDatastore._instance

    def get_default_background(self):
        return self.DEFAULT_BG_LOCATION

    def get_background_image(self):
        if self._background_image is None:
            self._read_preferences()
            background_path = str( self._preferences[self.PREF_BG_KEY] )
            self._background_image = Image.from_path(background_path)

        return self._background_image
    
    def get_scaled_background_image(self, width, height):
        if (self._scaled_image is None) or (width != self._scaled_width) or (height != self._scaled_height):
            self._scaled_image = self.get_background_image().copy()
            self._scaled_image.scale_to_best_fit(width, height)
            self._scaled_width = width
            self._scaled_height = height
        
        return self._scaled_image

    def set_background(self, new_background):
        filename = os.path.basename(new_background)
        destination_file = os.path.join(self.PREF_DIRNAME, filename)
        self._os_util.copy(new_background, destination_file)

        self._preferences[self.PREF_BG_KEY] = destination_file
        self._write_preferences()

        self._background_image = Image.from_path(destination_file)
        self._scaled_image = None

    def _read_preferences(self):
        try:
            with open(self._preferences_file, 'r') as f:
                self._preferences = json.load(f)
        except Exception as e:
            log.error("No file: " + self._preferences_file + ", using defaults", e)

        background_path = self.find_path_of_image()
        self._preferences = { self.PREF_BG_KEY: background_path }

    def _write_preferences(self):
        with open(self._preferences_file, 'w') as write_file:
            write_file.write(json.dumps(self._preferences))

    def find_path_of_image(self):
        filename = None

        if self._preferences is not None and self._preferences.has_key(self.PREF_BG_KEY):
            filename = self._preferences[self.PREF_BG_KEY]

        if filename is None or not self._file_exists(filename):
            filename = self.DEFAULT_BG_LOCATION

        return str(filename)

    def _file_exists(self, filename):
        return os.path.exists(filename)
