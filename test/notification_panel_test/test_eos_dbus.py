import unittest
from mock import Mock
from notification_panel.eos_dbus import Dbus


class DbusTestCase(unittest.TestCase):
    def test_get_interface(self):
        service = 'org.freedesktop.NetworkManager'
        object_path = '/org/freedesktop/NetworkManager'
        interface = 'org.freedesktop.NetworkManager'
        dbus = Mock()
        system_bus = Mock()
        struct = Mock()
        system_bus.get_object = Mock(return_value=struct)
        expected_interface = Mock()
        dbus.Interface = Mock(return_value=expected_interface)

        test_object = Dbus(dbus, system_bus)
        returned_interface = test_object.get_interface(service, object_path, interface)
        
        self.assertEquals(returned_interface, expected_interface)
        
