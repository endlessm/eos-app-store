import unittest
from mock import Mock
from search.search_box_model import SearchBoxModel

class TestSearchBoxModel(unittest.TestCase):

    def setUp(self):
        self.mock_manager = Mock()
        self.browser_launcher = self.mock_manager.browser_launcher
        self.url_validator = self.mock_manager.url_validator

        self.test_object = SearchBoxModel(Mock(return_value=self.browser_launcher), self.url_validator)

        self.url_validator.validate = Mock(return_value=True)

    def test_when_url_is_valid_then_browser(self):
        search_string = "blah"

        self.test_object.search(search_string)

        self.browser_launcher.launch_browser.assert_called_once_with(search_string)

    def test_when_url_is_valid_then_browser(self):
        self.url_validator.validate = Mock(return_value=False)
        search_string = "blah"

        self.test_object.search(search_string)

        self.browser_launcher.launch_search.assert_called_once_with(search_string)


    def test_launch_search_searches_google_if_empty_string_is_given(self):
        self.test_object.search('')

        self.browser_launcher.launch_browser.assert_called_once_with(self.test_object.DEFAULT_URL)

    def test_launch_search_searches_google_if_no_string_is_given(self):

        self.test_object.search(None)

        self.browser_launcher.launch_browser.assert_called_once_with(self.test_object.DEFAULT_URL)




