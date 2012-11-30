import unittest
from mock import Mock, call #@UnresolvedImport
from startup.remove_extra_files_task import RemoveExtraFilesTask

class RemoveExtraFilesTest(unittest.TestCase):
	def test_files_listed_are_removed(self):
		os_util = Mock()
		os_util.path = Mock()
		os_util.path.expanduser = Mock(return_value='some_path')
		os_util.remove = Mock()
		
		RemoveExtraFilesTask(os_util).execute()
		
		calls = []
		calls.append(call("some_path"))
		calls.append(call("some_path"))
		calls.append(call("some_path"))
		calls.append(call("some_path"))
		os_util.remove.assert_has_calls(calls, any_order=True)
		
		calls_to_expand = []
		calls_to_expand.append(call("~/application.list"))
		calls_to_expand.append(call("~/desktop.en_US"))
		calls_to_expand.append(call("~/desktop.pt_BR"))
		calls_to_expand.append(call("~/fluxbox-startup.log"))
		os_util.path.expanduser.assert_has_calls(calls_to_expand, any_order=True)
			
