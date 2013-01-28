import unittest
from mock import Mock
from taskbar_panel.xlib_helper import XlibHelper

class TestXlibHelper(unittest.TestCase):
    def setUp(self):
        self._mock_display = Mock()
        self._mock_logger = Mock()
        
        self._test_object = XlibHelper(self._mock_display, self._mock_logger)
        
        self._mock_display.reset_mock()
        
    def test_get_atom_id(self):
        atom_id = XlibHelper.Atom.ICON
        
        self._test_object.get_atom_id(atom_id)
        self._mock_display.intern_atom.assert_called_once_with(atom_id)
                
       
    def test_initially_try_to_get_window_name_from_property(self):
        window_name = unicode(Mock())
        
        self._window_name_atom_id = self._test_object.get_atom_id(XlibHelper.Atom.WINDOW_NAME)
        self._utf8_atom_id = self._test_object.get_atom_id(XlibHelper.Atom.UTF8)
        
        window = Mock()
        window_name_mock = Mock()
        window_name_mock.value = window_name
        window.get_full_property = Mock(return_value = window_name_mock)
        
        self.assertEquals(window_name, self._test_object.get_window_name(window))
        window.get_full_property.assert_called_once_with(self._window_name_atom_id, self._utf8_atom_id)

    def test_get_window_name_fallsback_on_python_lib_name_retrieval(self):
        window_name = unicode(Mock())
        
        self._window_name_atom_id = self._test_object.get_atom_id(XlibHelper.Atom.WINDOW_NAME)
        self._utf8_atom_id = self._test_object.get_atom_id(XlibHelper.Atom.UTF8)
        
        window = Mock()
        window.get_wm_name = Mock(return_value = window_name)
        window.get_full_property = Mock(side_effect = NameError)
        
        self.assertEquals(window_name, self._test_object.get_window_name(window))

    def test_get_window_name_returns_empty_string_if_all_else_fails(self):
        self._window_name_atom_id = self._test_object.get_atom_id(XlibHelper.Atom.WINDOW_NAME)
        self._utf8_atom_id = self._test_object.get_atom_id(XlibHelper.Atom.UTF8)
        
        window = Mock()
        window.get_wm_name = Mock(side_effect = Exception)
        window.get_full_property = Mock(side_effect = NameError)
        
        self.assertEquals("", self._test_object.get_window_name(window))
