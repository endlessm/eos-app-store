import unittest
from startup.initial_tasks import InitialTasks
from mock import Mock #@UnresolvedImport
import shutil
import os.path

from startup.firefox_tasks import FirefoxTasks
from startup.shotwell_tasks import ShotwellTasks
from startup.beatbox_tasks import BeatboxTasks
from startup.gimp_tasks import GimpTasks
from startup.windows_migration_tasks import WindowsMigrationTasks
from startup.remove_extra_directories_task import RemoveExtraDirectoriesTask
from startup.remove_extra_files_task import RemoveExtraFilesTask

from eos_log import log
from startup.delete_install_lock_task import DeleteInstallLockTask

class InitialTasksTest(unittest.TestCase):
    ENDLESS_DIR = os.path.expanduser("~/.endlessm")

    def setUp(self):
        self._clean_up()

        self._test_object = InitialTasks()
        self._test_object.TASK_PLUGINS = [Mock()]

    def tearDown(self):
        self._clean_up()

    def _clean_up(self):
        shutil.rmtree("/tmp/default_image", True)
        shutil.rmtree(self.ENDLESS_DIR, True)

    def test_initialize_tasks_are_correct(self):
        test_object = InitialTasks()

        self.assertEquals(8, len(test_object.TASK_PLUGINS))
        self.assertIsInstance(test_object.TASK_PLUGINS[0](), DeleteInstallLockTask)
        self.assertIsInstance(test_object.TASK_PLUGINS[1](), FirefoxTasks)
        self.assertIsInstance(test_object.TASK_PLUGINS[2](), ShotwellTasks)
        self.assertIsInstance(test_object.TASK_PLUGINS[3](), BeatboxTasks)
        self.assertIsInstance(test_object.TASK_PLUGINS[4](), GimpTasks)
        self.assertIsInstance(test_object.TASK_PLUGINS[5](), WindowsMigrationTasks)
        self.assertIsInstance(test_object.TASK_PLUGINS[6](), RemoveExtraDirectoriesTask)
        self.assertIsInstance(test_object.TASK_PLUGINS[7](), RemoveExtraFilesTask)

    def test_correct_tasks_are_called_when_perform_tasks_is_called(self):
        mock_task1 = Mock()
        mock_task1.execute = Mock()
        
        mock_task2 = Mock()
        mock_task2.execute = Mock()
        
        self._test_object.TASK_PLUGINS = [Mock(return_value=mock_task1), Mock(return_value=mock_task2)]

        self._test_object.perform_tasks()

        self.assertTrue(mock_task1.execute.called)
        self.assertTrue(mock_task2.execute.called)
        
    def test_if_there_are_errors_still_continue_executing_tasks(self):
        mock_task = Mock()
        mock_task.execute = Mock()
        
        error_class = Mock(side_effect=Exception())
        error_class.__name__ = ""
        
        self._test_object.TASK_PLUGINS = [error_class, Mock(return_value=mock_task)]

        self._test_object.perform_tasks()

        self.assertTrue(mock_task.execute.called)
        
    def test_if_there_are_errors_they_are_logged(self):
        orig_eos_error = log.error
        log.error = Mock()
        
        task_name = "this is the task name"
        error = Exception()
        
        mock_task_instance = Mock()
        mock_task_instance.execute = Mock(side_effect=error)
        
        mock_task_class = Mock(return_value=mock_task_instance)
        mock_task_class.__name__ = task_name
        
        
        self._test_object.TASK_PLUGINS = [mock_task_class]

        self._test_object.perform_tasks()

        log.error.assert_called_once_with("An error ocurred while executing " + task_name, error)
        
        log.error = orig_eos_error

    def test_initialized_file_is_created_after_running_perform_tasks(self):
        self._test_object.perform_tasks()

        self.assertTrue(os.path.exists(os.path.join(self.ENDLESS_DIR, ".initialized")))

    def test_dont_call_anything_if_system_is_already_initialized(self):
        os.makedirs(self.ENDLESS_DIR)
        open(os.path.join(self.ENDLESS_DIR, ".initialized"), "w").close()

        self._test_object.initialize_shotwell_settings = Mock()
        self._test_object.copy_default_images = Mock()

        self._test_object.perform_tasks()

        self.assertFalse(self._test_object.initialize_shotwell_settings.called)
        self.assertFalse(self._test_object.copy_default_images.called)

