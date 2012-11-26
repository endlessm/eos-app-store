import unittest
from mock import Mock #@UnresolvedImport
import os

from startup.auto_updates.endless_updater import EndlessUpdater
from eos_installer import endpoint_provider
from startup.auto_updates.install_notifier import InstallNotifier

class EndlessUpdaterTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_endless_downloader = Mock()
        self._mock_force_install = Mock()
        self._mock_force_install_checker = Mock()
        self._mock_install_notifier = Mock()

        self._test_object = EndlessUpdater(self._mock_endless_downloader, 
                                           self._mock_force_install,
                                           self._mock_force_install_checker,
                                           self._mock_install_notifier)
        
    def test_update_downloads_all_packages(self):
        self._test_object.update()
        
        self.assertTrue(self._mock_endless_downloader.download_all_packages.called)

    def test_update_should_inform_force_installer_checker_that_an_install_is_needed(self):
        self._test_object.update()
        
        self.assertTrue(self._mock_force_install_checker.need_to_do_install.called)

    def test_when_doing_updates_user_is_notified(self):
        self._test_object.update()
        
        self._mock_install_notifier.notify_user.assert_called_once_with()

    def test_do_not_install_all_packages_until_user_responds(self):
        self._mock_install_notifier.add_listener = Mock(side_effect=self._user_notifier_add_listener)
        
        self._test_object = EndlessUpdater(self._mock_endless_downloader, 
                                           self._mock_force_install,
                                            self._mock_force_install_checker,
                                           self._mock_install_notifier)
        
        self._mock_force_install.install_all_packages = Mock()
        self._test_object.update()

        self.assertFalse(self._mock_force_install.install_in_background.called, 
                         "Should not have installed all packages")

    def test_when_user_response_that_they_want_to_install_then_install_all_packages(self):
        self._mock_install_notifier.add_listener = Mock(side_effect=self._user_notifier_add_listener)
        
        self._test_object = EndlessUpdater(self._mock_endless_downloader, 
                                           self._mock_force_install,
                                           self._mock_force_install_checker,
                                           self._mock_install_notifier)
        
        self._mock_install_notifier.should_install = Mock(return_value=True)
        self._test_object.update()

        self._user_notified_listener()
        
        self.assertTrue(self._mock_force_install.install_in_background.called)
        
    def test_when_user_response_that_they_do_not_want_to_install_then_install_all_packages(self):
        self._mock_install_notifier.add_listener = Mock(side_effect=self._user_notifier_add_listener)
        
        self._test_object = EndlessUpdater(self._mock_endless_downloader, 
                                           self._mock_force_install,
                                           self._mock_force_install_checker,
                                           self._mock_install_notifier)
        
        self._mock_install_notifier.should_install = Mock(return_value=False)
        self._test_object.update()

        self._user_notified_listener()
        
        self.assertFalse(self._mock_force_install.install_in_background.called, 
                         "Should not have installed all packages")

    def _user_notifier_add_listener(self, *args, **kwargs):
        if args[0] == InstallNotifier.USER_RESPONSE:
            self._user_notified_listener = args[1]
    
    
    
