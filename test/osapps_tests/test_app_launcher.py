from mock import Mock
from unittest import TestCase
from osapps.app_launcher import AppLauncher

class AppLauncherTest(TestCase):
    def setUp(self):
        self._mock_os_util = Mock()
        self._test_object = AppLauncher(self._mock_os_util)
    
    def test_launch_executes_asynchronously(self):
        exec_name = "executable"
        
        self._test_object.launch(exec_name)
        
        self._mock_os_util.execute_async.assert_called_once_with([exec_name])
        
    def test_launch_file_executes_xdg_open_asynchronously(self):
        filename = "some file"
        
        self._test_object.launch_file(filename)
        
        self._mock_os_util.execute_async.assert_called_once_with(["xdg-open", filename])
        
    def test_array_vs_string(self):
        multi = "gedit"
        params = ["/home/dev1/.gitconfig"]
        single = "x-www-browser"
        
        self._test_object.launch(multi, params)
        self._mock_os_util.execute_async.assert_called_with([multi] + params)
        
        self._test_object.launch(single)
        self._mock_os_util.execute_async.assert_called_with([single])
        
