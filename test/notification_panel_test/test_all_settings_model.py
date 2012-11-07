import unittest
from mock import Mock #@UnresolvedImport

from notification_panel.all_settings_model import AllSettingsModel
from util.update_lock import UpdateLock
import threading

import time

class TestAllSettingsModel(unittest.TestCase):
    def setUp(self):
        self._mock_os_util = Mock()
        self._mock_app_launcher = Mock()
        self._mock_update_manager = Mock()
        
        self._test_object = AllSettingsModel(self._mock_os_util, self._mock_app_launcher, 
                                             self._mock_update_manager)
        
        self._cleanUp()
        
    def tearDown(self):
        self._cleanUp()
        
    def _cleanUp(self):
        UpdateLock().release()
    
    def test_get_current_version_uses_output_from_command_line_result(self):
        current_version = "version from desktop"

        self._mock_os_util.get_version = Mock(return_value=current_version)

        self.assertEquals("EndlessOS " + current_version, self._test_object.get_current_version())

    def test_when_using_command_line_ensure_that_the_correct_command_is_used(self):
        self._mock_os_util.execute = Mock(return_value="EndlessOS")

        self._test_object.get_current_version()

        self._mock_os_util.get_version.assert_called_once()
        
    def test_get_version_that_gets_none_does_not_break(self):
        self._mock_os_util.get_version = Mock(return_value=None)

        self.assertEquals("EndlessOS", self._test_object.get_current_version())

    def test_when_update_is_called_we_launch_updates(self):
        self._mock_update_manager.update_os = Mock()
        
        self._test_object.update_software()

        self.assertTrue(self._mock_update_manager.update_os.called)

    def test_when_restart_is_called_we_launch_restart(self):
        self._test_object.restart()

        self._mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.RESTART_COMMAND)

    def test_when_logout_is_called_we_launch_logout(self):
        self._test_object.logout()

        self._mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.LOGOUT_COMMAND)

    def test_when_shutdown_is_called_we_launch_shutdown(self):
        self._test_object.shutdown()

        self._mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.SHUTDOWN_COMMAND)

    def test_when_settings_is_called_we_launch_settings(self):
        self._test_object.open_settings()

        self._mock_app_launcher.launch.assert_called_once_with(AllSettingsModel.SETTINGS_COMMAND)

    def test_when_update_lock_is_locked_then_cant_update(self):
        UpdateLock().acquire()
        
        self.assertFalse(self._test_object.can_update())
        
    def test_when_update_lock_is_not_locked_then_can_update(self):
        self.assertTrue(self._test_object.can_update())
        
    def test_update_listener_ist_nofitied_when_an_update_lock_is_acquried(self):
        update_listener = Mock()
            
        test_object = AllSettingsModel()
        test_object.add_listener(AllSettingsModel.UPDATE_LOCK, update_listener)
        
        self.assertFalse(update_listener.called)
        
        UpdateLock().acquire()
        time.sleep(0.5)
        
        self.assertTrue(update_listener.called)
        
    def test_update_listener_ist_nofitied_when_an_update_lock_is_released(self):
        UpdateLock().acquire()
        
        update_listener = Mock()
            
        test_object = AllSettingsModel()
        test_object.add_listener(AllSettingsModel.UPDATE_LOCK, update_listener)
        
        self.assertFalse(update_listener.called)
        
        UpdateLock().release()
        time.sleep(0.5)
        
        self.assertTrue(update_listener.called)
        
    def test_on_delete_update_lock_thread_is_killed(self):
        test_object = AllSettingsModel()
        
        before = threading.active_count()
        test_object.__del__()
        after = threading.active_count()
        
        self.assertEquals(before - 1, after)
        