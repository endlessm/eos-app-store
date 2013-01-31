import unittest
from startup.startup_tasks import StartupTasks
from mock import Mock #@UnresolvedImport

from eos_log import log
from endless_core.auto_updates.force_install import ForceInstall
from startup.remove_extra_directories_task import RemoveExtraDirectoriesTask
from startup.remove_extra_files_task import RemoveExtraFilesTask
from endless_core.auto_updates.update_manager import UpdateManager

class StartupTasksTest(unittest.TestCase):
	
	def test_correct_default_tasks_exist(self):
		test_object = StartupTasks()
		self.assertEquals(2, len(test_object._all_tasks))
		self.assertIsInstance(test_object._all_tasks[0](), ForceInstall)
		self.assertIsInstance(test_object._all_tasks[1](), UpdateManager)

	def test_correct_tasks_are_called_when_perform_tasks_is_called(self):
		mock_task1 = Mock()
		mock_task1.execute = Mock()
		
		mock_task2 = Mock()
		mock_task2.execute = Mock()
		
		test_object = StartupTasks([Mock(return_value=mock_task1), Mock(return_value=mock_task2)])

		test_object.perform_tasks()

		self.assertTrue(mock_task1.execute.called)
		self.assertTrue(mock_task2.execute.called)
		
	def test_if_there_are_errors_still_continue_executing_tasks(self):
		mock_task = Mock()
		mock_task.execute = Mock()
		
		error_class = Mock(side_effect=Exception())
		error_class.__name__ = ""
		
		test_object = StartupTasks([error_class, Mock(return_value=mock_task)])

		test_object.perform_tasks()

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
		
		
		test_object = StartupTasks([mock_task_class])

		test_object.perform_tasks()

		log.error.assert_called_once_with("An error ocurred while executing " + task_name, error)
		
		log.error = orig_eos_error

