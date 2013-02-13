import unittest
from mock import Mock, patch
from search.search_box_presenter import SearchBoxPresenter
from search.search_box_constants import SearchBoxConstants

class TestSearchBoxPresenter(unittest.TestCase):

    def setUp(self):
        self.mock_manager = Mock()
        self.view = self.mock_manager.view
        self.model = self.mock_manager.model

        self.view.add_listener = Mock(side_effect=self._view_side_effect)

        SearchBoxPresenter(self.view, self.model)

    def _view_side_effect(self, *args, **kwargs):
        if args[0] == SearchBoxConstants.LAUNCH_BROWSER:
            self._launch_browser = args[1]

    def test_when_search_is_made_search_text_from_view_is_given_to_model(self):
        search_text = "search text"
        self.view.get_search_text = Mock(return_value=search_text)

        self._launch_browser()

        self.model.search.assert_called_once_with(search_text)

    def test_when_search_is_made_view_is_reset(self):
        self._launch_browser()

        self.assertTrue(self.view.reset_search.called)

