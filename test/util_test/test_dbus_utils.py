import unittest
from mock import Mock

from util.dbus_utils import DbusUtils

class DbusUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_dbus = Mock()
        self._mock_system_bus = Mock()
        self._mock_dbus.SystemBus = Mock(return_value=self._mock_system_bus)
        self._test_object = DbusUtils(self._mock_dbus)
        
    def test_get_system_bus_always_returns_static_system_bus(self):
        self._mock_dbus.SystemBus = Mock(return_value=None)
        
        self.assertEquals(self._test_object.get_system_bus(), self._mock_system_bus)
        self.assertEquals(DbusUtils(self._mock_dbus).get_system_bus(), self._mock_system_bus)
        self.assertEquals(DbusUtils(self._mock_dbus).get_system_bus(), self._mock_system_bus)

    # TODO test reg prop listener 
    
    def test_add_signal_callback_adds_signal_reciever_to_bus(self):
        def callback_function():
            pass 
        
        self._test_object.add_signal_callback(regex_match, callback_function)
        
        