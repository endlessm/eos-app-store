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

		self._test_object = Tasks()
		self._test_object.TASK_PLUGINS = [Mock()]

	def tearDown(self):
		self._clean_up()

	def _clean_up(self):
		shutil.rmtree("/tmp/default_image", True)
		shutil.rmtree(self.ENDLESS_DIR, True)

	def test_correct_tasks_are_called_when_perform_startup_tasks_is_called(self):
		mock_task1 = Mock()
		mock_task1.execute = Mock()
		
		mock_task2 = Mock()
		mock_task2.execute = Mock()
		
		self._test_object.TASK_PLUGINS = [Mock(return_value=mock_task1), Mock(return_value=mock_task2)]

		self._test_object.perform_startup_tasks()

		self.assertTrue(mock_task1.execute.called)
		self.assertTrue(mock_task2.execute.called)

	def test_initialized_file_is_created_after_running_perform_startup_tasks(self):

		self._test_object.perform_startup_tasks()

		self.assertTrue(os.path.exists(os.path.join(self.ENDLESS_DIR, ".initialized")))

	def test_dont_call_anything_if_system_is_already_initialized(self):
		os.makedirs(self.ENDLESS_DIR)
		open(os.path.join(self.ENDLESS_DIR, ".initialized"), "w").close()

		self._test_object.initialize_shotwell_settings = Mock()
		self._test_object.copy_default_images = Mock()

		self._test_object.perform_startup_tasks()

		self.assertFalse(self._test_object.initialize_shotwell_settings.called)
		self.assertFalse(self._test_object.copy_default_images.called)

