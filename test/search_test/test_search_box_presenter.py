import unittest
from mock import Mock, patch
from search.search_box_presenter import SearchBoxPresenter
from osapps.app_shortcut import AppShortcut

class TestSearchBoxPresenter(unittest.TestCase):

    def setUp(self):
        self.mock_app_launcher = Mock()

        self.testObject = SearchBoxPresenter(self.mock_app_launcher)

    def tearDown(self):
        pass

    def test_launch_search_launches_search(self):
        search_string = "blah"

        self.testObject.launch_search(search_string)

        self.mock_app_launcher.launch_search.assert_called_once_with(search_string)

    def test_launch_search_searches_google_if_empty_string_is_given(self):
        self.testObject.launch_search('')

        self.mock_app_launcher.launch_browser.assert_called_once_with("www.google.com")

    def test_launch_search_searches_google_if_no_string_is_given(self):
        self.testObject.launch_search(None)

        self.mock_app_launcher.launch_browser.assert_called_once_with("www.google.com")




