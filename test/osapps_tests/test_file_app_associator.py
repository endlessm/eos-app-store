from mock import Mock, call
from unittest import TestCase
from osapps.file_app_associator import FileAppAssociator

class FileAppAssociatorTest(TestCase):
    def setUp(self):
        self._mock_os_util = Mock()
        self._test_object = FileAppAssociator(self._mock_os_util)
    
    def test_this(self):
        mime_type = "some mime type"
        application = "application name"
        execute_results = [mime_type, application]
        def execute_results_side_effects(*args):
            return execute_results.pop(0)
        self._mock_os_util.execute = Mock(side_effect = execute_results_side_effects)
        
        filename = "some file"
        associated_app = self._test_object.associated_app(filename)
        
        self.assertEquals([call(["xdg-mime", "query", "filetype", filename]),
                          call(["xdg-mime", "query", "default", mime_type])], 
                          self._mock_os_util.execute.call_args_list)
        self.assertEqual(application, associated_app)