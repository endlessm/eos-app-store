import unittest
from mock import Mock

from taskbar_panel.predefined_icons_provider import PredefinedIconsProvider
from application_store.application_store_model import ApplicationStoreModel

class PredefinedIconsProviderTest(unittest.TestCase):
    def setUp(self):
        self._mock_gdk = Mock()
        self._mock_desktop_file_utils = Mock()

        self._icon1 = "Mini Icon 1"
        self._icon2 = "Mini Icon 2"
        self._icon3 = "Mini Icon 3"


        self._icon_path1 = "Icon Path 1"
        self._icon_path2 = "Icon Path 2"
        self._icon_path3 = "Icon Path 3"

        self._icon_map = { self._icon_path1 : self._icon1,
                           self._icon_path2 : self._icon2,
                           self._icon_path3 : self._icon3 }

        self._file_model1 = Mock()
        self._file_model1.class_name = Mock(return_value = "Classname 1")
        self._file_model1.mini_icon = Mock(return_value = self._icon_path1)

        self._file_model2 = Mock()
        self._file_model2.class_name = Mock(return_value = "Classname 2")
        self._file_model2.mini_icon = Mock(return_value = self._icon_path2)

        self._file_model3 = Mock()
        self._file_model3.class_name = Mock(return_value = "Classname 3")
        self._file_model3.mini_icon = Mock(return_value = self._icon_path3)

        self._app_models = [ self._file_model1, self._file_model2, self._file_model3 ]

        def get_app_models(path):
            self.assertEquals(path, ApplicationStoreModel.DEFAULT_APP_STORE_DIRECTORY)
            return self._app_models
        self._mock_desktop_file_utils.get_desktop_file_models = get_app_models

        def create_pixbuf(path):
            return self._icon_map[path]

        self._mock_gdk.pixbuf_new_from_file = create_pixbuf

        self._test_object = PredefinedIconsProvider(self._mock_gdk, self._mock_desktop_file_utils)

    def test_if_app_is_in_app_store_get_its_icon_path(self):
        self.assertEquals(self._test_object.get_icon_for("classname 1"), self._icon1)
        self.assertEquals(self._test_object.get_icon_for("classname 2"), self._icon2)
        self.assertEquals(self._test_object.get_icon_for("classname 3"), self._icon3)

    def test_if_app_is_not_in_app_store_then_return_none(self):
        self.assertEquals(self._test_object.get_icon_for("blargh"), None)
        self.assertEquals(self._test_object.get_icon_for("other blargh"), None)
