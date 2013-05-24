import time
from osapps.os_util import OsUtil
from unittest import TestCase
from mock import Mock #@UnresolvedImport

class OsUtilTest(TestCase):
    _file_name1 = "/tmp/os_util_test1.txt"
    _file_name2 = "/tmp/os_util_test2.txt"
    
    def setUp(self):
        self._test_object = OsUtil()
    
    def test_execute_command(self):
        output = self._test_object.execute(["echo", "-n", "foo", "bar"])
        self.assertEqual("foo bar", output)
        
    def test_execute_command_with_error(self):
        try:
            OsUtil.execute(["asdf"])
            self.fail("Should have thrown exception")
        except:
            pass
      
    def test_execute_async_calls_Pcall(self):
        self._test_object.execute_async(["touch", self._file_name1])
        time.sleep(1)
        self.assertEqual(self._file_name1, OsUtil().execute(["ls", self._file_name1]))
        
        self._test_object.execute(["rm","-rf", self._file_name1])      
    
    def test_execute_copy_copies(self):
        expected_content = "asdffasdfdasfasdf"
        open(self._file_name1, "w").write(expected_content)
        
        self._test_object.copy(self._file_name1, self._file_name2)
        
        self.assertEqual(expected_content, open(self._file_name2, "r").read()) 
        
    def test_when_get_version_is_called_we_return_version(self):
        self._test_object.execute = Mock(return_value='osversion')
        
        actual_version = self._test_object.get_version()
        
        self._test_object.execute.assert_called_once_with(self._test_object.VERSION_COMMAND)
        
        self.assertEquals(actual_version, "osversion")
        
    def test_when_get_version_is_called_and_it_blows_up_we_return_unknown(self):
        self._test_object.execute = Mock(side_effect=Exception('abc'))
        
        self.assertIsNone(self._test_object.get_version())        
        
