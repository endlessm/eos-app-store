import unittest
from notification_panel.version_provider import VersionProvider
import json
from osapps.os_util import OsUtil

class TestVersionProvider(unittest.TestCase):
    _filename = "/tmp/version.json"
    _current_version = "endless os version"
    _server_endpoint = "server endpoint"
    
    def setUp(self):
        file_data = {
                          "version":self._current_version,
                          "server_endpoint":self._server_endpoint
                    }

        file_content = json.dumps(file_data)
        with open(self._filename, "w") as f:
            f.write(file_content)
        self.test_object = VersionProvider(self._filename)

    def tearDown(self):
        OsUtil().execute(["rm", "-f", self._filename])
    
    def test_get_current_version_returns_version_from_file(self):
        self.assertEquals(self._current_version, self.test_object.get_current_version())
        
    def test_get_current_version_returns_None_when_version_is_not_in_file(self):
        self.tearDown()
        file_data = {
                          "server_endpoint":self._server_endpoint
                    }

        file_content = json.dumps(file_data)
        with open(self._filename, "w") as f:
            f.write(file_content)
        self.test_object = VersionProvider(self._filename)
        
        self.assertEquals(None, self.test_object.get_current_version())
    
    def test_get_server_endpoint_returns_server_endpoint_from_file(self):
        self.assertEquals(self._server_endpoint, self.test_object.get_server_endpoint())

    def test_get_server_endpoint_returns_None_when_server_endpoint_is_not_in_file(self):
        self.tearDown()
        file_data = {
                          "version":self._current_version
                    }

        file_content = json.dumps(file_data)
        with open(self._filename, "w") as f:
            f.write(file_content)
        self.test_object = VersionProvider(self._filename)
        
        self.assertEquals(None, self.test_object.get_server_endpoint())
        
#    def test_get_current_version_uses_output_from_command_line_result(self):
#        current_version = "version from browser"
#
#        mock_os_util = Mock()
#        mock_os_util.execute = Mock(return_value=current_version)
#
#        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt")
#
#        self.assertEquals("EndlessOS " + current_version, test_object.get_current_version())
#
#    def test_when_using_command_line_ensure_that_the_correct_command_is_used(self):
#        mock_os_util = Mock()
#        mock_os_util.execute = Mock(return_value="")
#
#        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt")
#
#        test_object.get_current_version()
#
#        mock_os_util.execute.assert_called_once_with(AllSettingsModel.VERSION_COMMAND)
#
#    def test_when_using_command_line_and_an_error_occurs_then_just_display_endlessos(self):
#        mock_os_util = Mock()
#        mock_os_util.execute = Mock(side_effect=Exception("boom!"))
#
#        test_object = AllSettingsModel(mock_os_util, "file_that_doesn't exist.txt")
#
#        self.assertEquals("EndlessOS", test_object.get_current_version())


    