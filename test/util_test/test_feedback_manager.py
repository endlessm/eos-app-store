import unittest
from mock import Mock

from util.feedback_manager import FeedbackManager

class FeedbackManagerTestCase(unittest.TestCase):
    def setUp(self):
        self._metrics_pool_mock = Mock()
        self.test_object = FeedbackManager(self._metrics_pool_mock)
        
    def test_send_feedback_data(self):
        mock_conn = Mock()
        self.test_object._create_connection = Mock(return_value=mock_conn)
        message_text = "foo bar"
        is_bug = True
        timestamp = 101
        
        data = self._create_json(message_text, timestamp, is_bug)
        
        self.test_object.write_data(data)
        
        self._metrics_pool_mock.launch_async.assert_called_once_with([data, "feedback.json", mock_conn])

    def _create_json(self, message, timestamp, is_bug):
        return {'message': message, 'timestamp': timestamp, 'bug': is_bug}

