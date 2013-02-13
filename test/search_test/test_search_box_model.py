import unittest
from mock import Mock
from search.search_box_model import SearchBoxModel

class TestSearchBoxModel(unittest.TestCase):

    def setUp(self):
        self.mock_app_launcher = Mock()

        self.testObject = SearchBoxModel(self.mock_app_launcher)

    def test_launch_search_launches_search(self):
        search_string = "blah"

        self.testObject.search(search_string)

        self.mock_app_launcher.launch_search.assert_called_once_with(search_string)

    def test_launch_search_searches_google_if_empty_string_is_given(self):
        self.testObject.search('')

        self.mock_app_launcher.launch_browser.assert_called_once_with("www.google.com")

    def test_launch_search_searches_google_if_no_string_is_given(self):
        self.testObject.search(None)

        self.mock_app_launcher.launch_browser.assert_called_once_with("www.google.com")




