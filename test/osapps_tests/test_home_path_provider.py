import unittest
import os
from osapps.home_path_provider import HomePathProvider

class HomePathProviderTest(unittest.TestCase):
    def setUp(self):
        self._go_english()

    def _go_english(self):
        os.environ["LANG"] =  "en_US.UTF-8"
        os.environ["LANGUAGE"] =  "en_US.UTF-8"

    def _go_portuguese(self):
        os.environ["LANG"] =  "pt_BR.UTF-8"
        os.environ["LANGUAGE"] =  "pt_BR.UTF-8"

    def tearDown(self):
        self._go_english()

    def test_get_user_directory_returns_directory_name(self):
        pictures_folder = HomePathProvider().get_user_directory('Pictures')
        self.assertEquals(os.path.expanduser('~/Pictures'), pictures_folder)

    def test_get_user_directory_returns_non_mapped_data(self):
        pictures_folder = HomePathProvider().get_user_directory('testdir')
        self.assertEquals(os.path.expanduser('~/testdir'), pictures_folder)

    def test_get_user_directory_returns_home_directory_when_no_path_is_given(self):
        home_path = HomePathProvider().get_user_directory()
        self.assertEquals(os.path.expanduser('~'), home_path)

    def test_get_images_directory_returns_localized_images_directory_name(self):
        self._go_portuguese()

        pictures_folder = HomePathProvider().get_pictures_directory()
        self.assertEquals(os.path.expanduser('~/Imagens'), pictures_folder)

    def test_get_videos_directory_returns_videos_directory_name(self):
        pictures_folder = HomePathProvider().get_videos_directory()
        self.assertEquals(os.path.expanduser('~/Videos'), pictures_folder)

    def test_get_documents_directory_returns_documents_directory_name(self):
        pictures_folder = HomePathProvider().get_documents_directory()
        self.assertEquals(os.path.expanduser('~/Documents'), pictures_folder)

    def test_get_images_directory_with_other_folder_returns_localized_images_directory_name(self):
        self._go_portuguese()

        pictures_folder = HomePathProvider().get_pictures_directory('monkey')
        self.assertEquals(os.path.expanduser('~/Imagens/monkey'), pictures_folder)

    def test_get_music_directory_with_other_folder_returns_localized_music_directory_name(self):
        self._go_portuguese()

        music_folder = HomePathProvider().get_music_directory('foo')
        self.assertEquals(os.path.expanduser('~/M\xc3\xbasica/foo'), music_folder)

    def test_get_music_directory_returns_localized_music_directory_name(self):
        self._go_portuguese()

        music_folder = HomePathProvider().get_music_directory()
        self.assertEquals(os.path.expanduser('~/M\xc3\xbasica'), music_folder)

