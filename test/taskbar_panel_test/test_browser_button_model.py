import unittest
from mock import Mock

from taskbar_panel.browser_button_model import BrowserButtonModel

class BrowserButtonModelTest(unittest.TestCase):
   def setUp(self):
      self._mock_locale_util = Mock()
      self._test_object = BrowserButtonModel(self._mock_locale_util)

   def test_url_contains_exploration_center(self):
      self.assertTrue("file:/" in self._test_object.get_exploration_center_url())
      self.assertTrue("exploration_center" in self._test_object.get_exploration_center_url())

   def test_url_contains_correct_locale(self):
      locale = "this is the locale"
      self._mock_locale_util.get_locale = Mock(return_value=locale)

      self.assertTrue(locale in self._test_object.get_exploration_center_url())
