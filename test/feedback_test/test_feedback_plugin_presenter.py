import unittest
from mock import Mock, patch
from feedback.feedback_plugin_presenter import FeedbackPluginPresenter

class TestEndlessDesktopPresenter(unittest.TestCase):

    def setUp(self):
        self.mock_model = Mock()

        self.testObject = FeedbackPluginPresenter(self.mock_model)

    def tearDown(self):
        pass

    def test_submit_feedback_updates_model(self):
        message = "some text"
        is_bug = True

        self.testObject.submit_feedback(message, is_bug)

        self.mock_model.submit_feedback.assert_called_once_with(message, is_bug)

