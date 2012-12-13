import unittest
from startup.remove_extra_directories_task import RemoveExtraDirectoriesTask
from mock import Mock, call #@UnresolvedImport

class RemoveExtraDirectoriesTest(unittest.TestCase):
    def test_directories_listed_are_removed(self):
        os_util = Mock()
        os_util.path = Mock()
        os_util.path.expanduser = Mock(return_value='some_path')
        sh_util = Mock()
        sh_util.rmtree = Mock()
        
        RemoveExtraDirectoriesTask(os_util, sh_util).execute()
        
        calls = []
        calls.append(call("some_path"))
        calls.append(call("some_path"))
        sh_util.rmtree.assert_has_calls(calls, any_order=True)
        
        calls_to_expand = []
        # For now, we just call with English and Portuguese folder names
        # TODO Consider refactoring to use the home path provider based on gettext
        calls_to_expand.append(call("~/Public"))
        calls_to_expand.append(call("~/Templates"))
        calls_to_expand.append(call("~/P\xc3\xbablico"))
        calls_to_expand.append(call("~/Modelos"))
        os_util.path.expanduser.assert_has_calls(calls_to_expand, any_order=True)
