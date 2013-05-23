from EosAppStore.osapps.os_util import OsUtil
import os.path

class HomePathProvider():
    PREFIX = '~'

    def __init__(self, os_util=OsUtil()):
        self.os_util = os_util

    def get_videos_directory(self, *args):
        return self._add_prefix_to_path("Videos", args)

    def get_documents_directory(self, *args):
        return self._add_prefix_to_path("Documents", args)

    def get_user_directory(self, *args):
        return self._get_path(list(args))

    def get_music_directory(self, *args):
        return self._add_prefix_to_path("Music", args)

    def get_pictures_directory(self, *args):
        return self._add_prefix_to_path("Pictures", args)

    def _add_prefix_to_path(self, folder, args):
        args = list(args)
        args.insert(0, folder)
        return self._get_localized_path(args)

    def _get_localized_path(self, args):
        path_elements = args[1:]
        path_elements.insert(0, self._translate_folder(args[0]))
        return self._get_path(path_elements)

    def _translate_folder(self, folder):
        return self.os_util.execute(["gettext", "-d", "xdg-user-dirs", folder])

    def _get_path(self, args):
        args.insert(0, self.PREFIX)
        return os.path.expanduser(os.path.join(*args))


