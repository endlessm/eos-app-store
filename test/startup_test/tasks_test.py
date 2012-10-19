import unittest
from startup.tasks import Tasks
from mock import Mock, call
import shutil
import os
import os.path

class TasksTest(unittest.TestCase):
	ENDLESS_DIR = os.path.expanduser("~/.endlessm")

	def setUp(self):
		self._clean_up()
		os.makedirs(self.ENDLESS_DIR)

		self._mock_home_path_provider = Mock()
		self._test_object = Tasks(self._mock_home_path_provider)

		self._orig_copytree = shutil.copytree
		self._mock_copytree = Mock()
		shutil.copytree = self._mock_copytree

	def tearDown(self):
		self._clean_up()

		shutil.copytree = self._orig_copytree

	def _clean_up(self):
		shutil.rmtree(self.ENDLESS_DIR, True)

	def test_correct_tasks_are_called_when_perform_startup_tasks_is_called(self):
		self._test_object.initialize_shotwell_settings = Mock()
		self._test_object.copy_default_images = Mock()

		self._test_object.perform_startup_tasks()

		self.assertTrue(self._test_object.initialize_shotwell_settings.called)
		self.assertTrue(self._test_object.copy_default_images.called)

	def test_initialized_file_is_created_after_running_perform_startup_tasks(self):
		self._test_object.initialize_shotwell_settings = Mock()
		self._test_object.copy_default_images = Mock()

		self._test_object.perform_startup_tasks()

		self.assertTrue(os.path.join(self.ENDLESS_DIR, ".initialized"))

	def test_dont_call_anything_if_system_is_already_initialized(self):
		open(os.path.join(self.ENDLESS_DIR, ".initialized"), "w").close()

		self._test_object.initialize_shotwell_settings = Mock()
		self._test_object.copy_default_images = Mock()

		self._test_object.perform_startup_tasks()

		self.assertFalse(self._test_object.initialize_shotwell_settings.called)
		self.assertFalse(self._test_object.copy_default_images.called)

	def test_initializing_shotwell_settings(self):
		mock_os_util = Mock()
		mock_os_util.execute = Mock()

		self._test_object.initialize_shotwell_settings(mock_os_util)

		mock_os_util.execute.assert_has_calls([
				call(["gsettings", "set", "org.yorba.shotwell.preferences.ui", "show-welcome-dialog", "false"]), 
				call(["gsettings", "set", "org.yorba.shotwell.preferences.files", "auto-import", "true"])
				])

	def test_get_pictures_directory_from_home_path_provider(self):
		self._mock_home_path_provider.get_user_directory = Mock()

		self._test_object.copy_default_images()

		self._mock_home_path_provider.get_user_directory.assert_called_once_with("Pictures")

	def test_copy_default_images(self):
		pictures_directory = "pictures directory"
		self._mock_home_path_provider.get_user_directory = Mock(return_value=pictures_directory)

		self._test_object.copy_default_images()

		self._mock_copytree.assert_called_once_with("/usr/share/endlessm/default_images", pictures_directory)

