import unittest
from mock import Mock
from add_shortcuts_module.add_shortcuts_presenter import AddShortcutsPresenter
from osapps.app_shortcut import AppShortcut
from desktop_files.application_model import ApplicationModel
from desktop_files.link_model import LinkModel

class TestAddShortcutsPresenter(unittest.TestCase):
    def setUp(self):
        self.mock_model = Mock()
        self.mock_model.get_category_data = Mock(return_value=[])
        self.mock_app_store_model = Mock()
        self.mock_app_store_model.get_categories = Mock(return_value=[])
        self.mock_recommended_sites_provider = Mock()

        self.mock_format_util = Mock()
        self.mock_format_util.format = Mock(return_value='')

        self._mock_connection= Mock()
        self._mock_connection.read = Mock(return_value="abc")
        self._mock_connection.geturl = Mock(return_value="http://facebook.com/favicon.ico")
        
        self._mock_pixbuf_loader = Mock(return_value = "pixbuf")
        
        def mock_connection_callback(url):
            print url
            if url == "http://facebook.com" or url == "http://facebook.com/favicon.ico":
                return self._mock_connection
            else:
                return None
        
        self._mock_url_connector = mock_connection_callback
        self._mock_view = Mock()
        self.test_object = AddShortcutsPresenter(view = self._mock_view)
        self.test_object._model = self.mock_model
        self.test_object._app_store_model = self.mock_app_store_model
        self.test_object._sites_provider = self.mock_recommended_sites_provider
        self.test_object._name_format_util = self.mock_format_util

        self.path = '/tmp/'
        self.hint = 'blah'
        self.available_app_shortcuts = [
                                        AppShortcut(123, "App", "", []),
                                        AppShortcut(234, "App 1", "", []),
                                        AppShortcut(345, "App 2", "", [])
                                        ]
        self.application_categories = ['AUDIO', 'VIDEO', 'MEDIA']


    def test_get_category_data(self):
        self.test_object.get_category_data()
        self.test_object._app_store_model.get_categories.assert_called_once()
        self.test_object._model.get_category_data.assert_called_once()

    def test_get_folder_icons(self):
        self.test_object.get_folder_icons(self.path, self.hint)
        self.mock_model.get_folder_icons.assert_called_once_with(self.path, self.hint, '')

    def test_create_directory(self):
        mock_datastore = Mock()
        mock_datastore.get_all_shortcuts = Mock(return_value=self.available_app_shortcuts)
        dir_name = 'blah'
        self.test_object.create_directory(dir_name, '/tmp/image.svg', mock_datastore)
        self.mock_model.create_directory.assert_called_once_with(dir_name)
        mock_datastore.get_all_shortcuts.assert_called_once_with(True)
        mock_datastore.add_shortcut.assert_called_once()
        self._mock_view.close.assert_called_once_with()
        
    def test_add_shortcut(self):
        mock_datastore = Mock()
        shortcut = Mock()
        self.test_object.add_shortcut(shortcut, mock_datastore)
        mock_datastore.add_shortcut.called_once_with(shortcut)
        self._mock_view.close.assert_called_once_with()
        
    def test_check_dir_name(self):
        expected_value = 'App 3'
        self.assertEqual(expected_value, self.test_object.check_dir_name('App', self.available_app_shortcuts))

    def test_get_category(self):
        category = 'Dummy category'
        self.test_object.get_category(category)
        self.mock_app_store_model.get_categories.assert_called_once(category)

    def test_get_recommended_sites(self):
        self.test_object._sites_provider.get_recommended_sites()
        self.mock_recommended_sites_provider.get_recommended_sites.assert_called_once()

    def test_set_add_shortcuts_box(self):
        category = 'Dummy category'
        subcategory = 'Dummy subcategory'
        self.test_object.set_add_shortcuts_box(category, subcategory)
        self._mock_view.set_add_shortcuts_box.assert_called_once_with(category, subcategory)

    def test_install_app(self):
        app = ApplicationModel('dummy', 'dummy', [])
        self.test_object.install_app(app)
        self.test_object._app_store_model.install.assert_called_once_with(app)

    def test_install_site(self):
        name = 'Facebook'
        url = 'facebook.com'
        comment = 'Blah, blah...'

        site = LinkModel('', url, name, comment)
        self.test_object.get_favicon_image_file = Mock()
        self.test_object.build_shortcut_from_link_model(site)
        self.test_object.get_favicon_image_file.assert_called_once_with(site._url)
        self.test_object._name_format_util.format.assert_called_once_with(site._name)

    def test_get_favicon(self):
        self.test_object = AddShortcutsPresenter(self._mock_url_connector, self._mock_pixbuf_loader)
        self.test_object._sites_provider = self.mock_recommended_sites_provider
        self.test_object._is_image_in_cache = Mock(return_value = False)
        
        url = 'facebook.com'
        self.assertEquals('pixbuf', self.test_object.get_favicon(url))
        self.assertTrue(self._mock_connection.close.called)       
        
        url = 'dummy.url.kom'
        result = self.test_object.get_favicon(url)
        self.assertFalse(result)

    def test_get_favicon_image_file(self):
        url = 'facebook.com'
        result = self.test_object.get_favicon_image_file(url)
        self.assertTrue(result)
        self.assertTrue(isinstance(result, str))
        url = 'dummy.url.kom'
        result = self.test_object.get_favicon_image_file(url)
        self.assertFalse(result)

    def test_get_custom_site_shortcut_when_unknown_site(self):
        self.test_object = AddShortcutsPresenter(self._mock_url_connector)
        self.test_object._sites_provider = self.mock_recommended_sites_provider
 
        url = 'facebook.com'
        self.mock_recommended_sites_provider.get_recommended_sites = Mock(return_value=[Mock()])
        result = self.test_object.create_link_model(url)
        
        self.assertTrue(result)
        self.assertTrue(isinstance(result, LinkModel))
        self.assertTrue(self._mock_connection.close.called)

        url = 'dummy.url.kom'
        result = self.test_object.create_link_model(url)
        self.assertFalse(result)

    def test_get_custom_site_shortcut_when_known_site(self):
        url = 'facebook.com'
        facebook_model = LinkModel(url, url, "http://"+url)
        self.mock_recommended_sites_provider.get_recommended_sites = Mock(return_value=[facebook_model])
        result = self.test_object.create_link_model(url)
        self.assertEquals(result, facebook_model)

    def test_strip_protocol(self):
        full = 'http://facebook.com'
        full_ssl = 'https://facebook.com'
        stripped = 'facebook.com'
        result = self.test_object._strip_protocol(full)
        self.assertEqual(result, stripped)
        result = self.test_object._strip_protocol(full_ssl)
        self.assertEqual(result, stripped)
        result = self.test_object._strip_protocol(stripped)
        self.assertEqual(result, stripped)
