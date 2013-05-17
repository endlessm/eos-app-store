from mock import Mock
from application_store.installed_applications_model import InstalledApplicationsModel
import os
import json
import unittest
import shutil
import tempfile


class InstalledApplicationsModelTestCase(unittest.TestCase):

    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()
        self._app_store_dir = self._temp_dir
        self._test_object = InstalledApplicationsModel()
        self._test_object.set_data_dir(self._app_store_dir)

    def tearDown(self):
        try:
            shutil.rmtree(self._tmp_dir, True)
        except:
            pass

    def _make_file(self, dirname, filename, content = 'Testing'):
        f = open(os.path.join(dirname, filename), 'w')
        f.write(content)
        f.close()

    def test_no_file_gives_empty_model(self):
        installed_apps = self._test_object.installed_applications()
        self.assertIsNotNone(installed_apps)
        self.assertEquals(0, len(installed_apps))

    def test_reading_zero_length_array_from_file(self):
        self._make_file(self._app_store_dir, 'installed_applications.json', '{}')
        self._test_object.set_data_dir(self._app_store_dir)
        installed_apps = self._test_object.installed_applications()
        self.assertIsNotNone(installed_apps)
        self.assertEquals(0, len(installed_apps))

    def test_reading_single_item_array_from_file(self):
        self._make_file(self._app_store_dir, 'installed_applications.json', '["foo"]')
        self._test_object.set_data_dir(self._app_store_dir)
        installed_apps = self._test_object.installed_applications()
        self.assertIsNotNone(installed_apps)
        self.assertEquals(1, len(installed_apps))
        self.assertEquals('foo', installed_apps[0])

    def test_reading_multiple_items_array_from_file(self):
        self._make_file(self._app_store_dir, 'installed_applications.json', '["foo", "bar"]')
        self._test_object.set_data_dir(self._app_store_dir)
        installed_apps = self._test_object.installed_applications()
        self.assertIsNotNone(installed_apps)
        self.assertEquals(2, len(installed_apps))
        self.assertIn('foo', installed_apps)
        self.assertIn('bar', installed_apps)
        
    def test_files_remain_ordered(self):
        installed_apps = self._test_object.installed_applications()
        self.assertIsNotNone(installed_apps)
        self.assertEquals(0, len(installed_apps))
        self._test_object.install('foo')
        full_path = os.path.join(self._app_store_dir, 'installed_applications.json')
        self.assertTrue(os.path.isfile(full_path))
        self.assertEquals(['foo'], json.load(open(full_path, "r")))
        self._test_object.install('bar')
        self.assertEquals(['foo', 'bar'], json.load(open(full_path, "r")))
        self._test_object.install('baz')
        self.assertEquals(['foo', 'bar', 'baz'], json.load(open(full_path, "r")))
        self._test_object.uninstall('bar')
        self.assertEquals(['foo', 'baz'], json.load(open(full_path, "r")))
        self._test_object.install_at('bar', 1)
        self.assertEquals(['foo', 'bar', 'baz'], json.load(open(full_path, "r")))

    def test_installing_an_application_creates_file(self):
        self._test_object.install('foo')

        self.assertIn('foo', self._test_object.installed_applications())
        self._verify_file_content(['foo'])

    def test_uninstalling_an_application_removes_it_from_file(self):
        self._test_object.install('foo')
        self._test_object.install('bar')

        self._test_object.uninstall('foo')

        self.assertIn('bar', self._test_object.installed_applications())
        self._verify_file_content(['bar'])

    def test_is_installed(self):
        self.assertFalse(self._test_object.is_installed('not-installed'))
        self._test_object.install('newly-installed')
        self.assertTrue(self._test_object.is_installed('newly-installed'))
        self._test_object.uninstall('newly-installed')
        self.assertFalse(self._test_object.is_installed('newly-installed'))

    def _verify_file_content(self, expected):
        full_path = os.path.join(self._app_store_dir, 'installed_applications.json')
        self.assertTrue(os.path.isfile(full_path))
        json_data = json.load(open(full_path, "r"))
        self.assertIsNotNone(json_data)
        for app in expected:
            self.assertIn(app, json_data)
            

