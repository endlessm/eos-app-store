import unittest
from feedback.feedback_plugin_model import FeedbackPluginModel
from mock import Mock #@UnresolvedImport

class FeedbackPluginModelTestCase(unittest.TestCase):
    def setUp(self):
        self.mock_feedback_manager = Mock()
        self.mock_time_provider = Mock()
        self.mock_time_provider.get_current_time = Mock(return_value="12:00")
        self.testObject = FeedbackPluginModel(self.mock_feedback_manager, self.mock_time_provider)

    def test_send_feedback(self):
        message = "foo bar baz"
        bug = False
        self.testObject.submit_feedback(message, bug)

        expected = {"message":message, "timestamp":"12:00", "bug":bug}

        self.mock_feedback_manager.write_data.assert_called_once_with(expected)

