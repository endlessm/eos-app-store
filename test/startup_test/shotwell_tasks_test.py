import unittest
from mock import Mock, call

from startup.shotwell_tasks import ShotwellTasks

<<<<<<< HEAD
class TasksTest(unittest.TestCase):
	ENDLESS_DIR = os.path.expanduser("~/.endlessm")

	def setUp(self):
		self._clean_up()
		os.makedirs(self.ENDLESS_DIR)

		self._mock_home_path_provider = Mock()
		self._mock_home_path_provider.get_user_directory = Mock(return_value="")
		self._mock_os_util = Mock()
		self._mock_os_util.execute = Mock()
		
		self._test_object = ShotwellTasks(self._mock_home_path_provider, self._mock_os_util)
		shutil.rmtree("/tmp/default_image", True)
		os.makedirs("/tmp/default_image")
		open("/tmp/default_image/test.image", "w").close()
		def default_images_stub():
			return "/tmp/default_image/*"
		self._test_object._default_images_directory = default_images_stub


		self._orig_copy = shutil.copy2
		self._mock_copy = Mock()
		shutil.copy2 = self._mock_copy

	def tearDown(self):
		self._clean_up()

		shutil.copy2 = self._orig_copy

	def _clean_up(self):
		shutil.rmtree("/tmp/default_image", True)
		shutil.rmtree(self.ENDLESS_DIR, True)

	def test_initializing_shotwell_settings(self):
		self._test_object.execute()

		self._mock_os_util.execute.assert_has_calls([
				call(["gsettings", "set", "org.yorba.shotwell.preferences.ui", "show-welcome-dialog", "false"]), 
				call(["gsettings", "set", "org.yorba.shotwell.preferences.files", "auto-import", "true"])
				])

	def test_get_pictures_directory_from_home_path_provider(self):
		self._mock_home_path_provider.get_user_directory = Mock(return_value="")

		self._test_object.execute()

		self._mock_home_path_provider.get_user_directory.assert_called_once_with("Pictures")

	def test_copy_default_images(self):
		pictures_directory = "pictures directory"
		endless_pictures_directory = os.path.join(pictures_directory, "Endless")
		self._mock_home_path_provider.get_user_directory = Mock(return_value=pictures_directory)

		self._test_object.execute()

		self._mock_copy.assert_called_once_with("/tmp/default_image/test.image", os.path.join(endless_pictures_directory, "test.image"))

=======
class ShotwellTaskTest(unittest.TestCase):
    def setUp(self):
        self.home_directory_copier = Mock()
        self.os_util = Mock()
        self.os_util.execute = Mock()
        self.home_path = "home_path"
        self.home_path_provider = Mock(return_value =
                self.home_path)

        self.test_object = ShotwellTasks(self.home_directory_copier, self.os_util)

    def test_default_location_is_correct(self):
        self.assertEquals("/usr/share/endlessm-default-files/default_images",
                self.test_object._default_images_folder_path())

    def test_target_dir_is_correct(self):
        self.assertEqual('Pictures', self.test_object.TARGET_DIR)

    def test_gsettings_are_set_for_shotwell(self):
        self.test_object.execute()
        self.os_util.execute.assert_has_calls([
                call(["gsettings", "set", "org.yorba.shotwell.preferences.ui", "show-welcome-dialog", "false"]),
                call(["gsettings", "set", "org.yorba.shotwell.preferences.files", "auto-import", "true"])
                ])

    def test_file_copier_is_called_with_default_images_folder(self):
        self.test_object.execute()
        self.home_directory_copier.copy_from.assert_called_once_with(self.test_object._default_images_folder_path())
>>>>>>> release_1.0.16
