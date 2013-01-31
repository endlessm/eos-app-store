import unittest
from mock import Mock, patch
from social_bar.social_bar_presenter import SocialBarPresenter
from osapps.app_shortcut import AppShortcut

class TestSocialBarPresenter(unittest.TestCase):

    def setUp(self):
        self.mock_app_launcher = Mock()

        self.testObject = SocialBarPresenter(self.mock_app_launcher)

    def tearDown(self):
        pass

    def test_launch_social_launches_social(self):
        social_path = "/usr/bin/eos-social"

        self.testObject.launch()

        self.mock_app_launcher.launch.assert_called_once_with(social_path)



