import unittest
from mock import Mock
from application_store.category_model import CategoryModel
from sets import ImmutableSet
import tempfile
from application_store.installed_applications_model import InstalledApplicationsModel
import shutil
import os
import json


class InstalledApplicationsModelTestCase(unittest.TestCase):
    
    def setUp(self):
        self._app_store_dir = tempfile.mkdtemp()
        self._test_object = InstalledApplicationsModel(self._app_store_dir)

    def tearDown(self):
        # Remove the temporary directories
        shutil.rmtree(self._app_store_dir)

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
        self._make_file(self._app_store_dir, 'installed_applications.json', '{"installed_applications":["foo"]}')
        self._test_object.set_data_dir(self._app_store_dir)
        installed_apps = self._test_object.installed_applications()
        self.assertIsNotNone(installed_apps)
        self.assertEquals(1, len(installed_apps))
        self.assertEquals('foo', installed_apps[0])
        
    def test_reading_multiple_items_array_from_file(self):
        self._make_file(self._app_store_dir, 'installed_applications.json', '{"installed_applications":["foo", "bar"]}')
        self._test_object.set_data_dir(self._app_store_dir)
        installed_apps = self._test_object.installed_applications()
        self.assertIsNotNone(installed_apps)
        self.assertEquals(2, len(installed_apps))
        self.assertIn('foo', installed_apps)
        self.assertIn('bar', installed_apps)
        
    def test_installing_an_application(self):
        self._test_object.install('foo')

        self.assertIn('foo', self._test_object.installed_applications())
            
    def test_installing_an_application_creates_file(self):
        self._test_object.install('foo')

        self.assertIn('foo', self._test_object.installed_applications())
        full_path = os.path.join(self._app_store_dir, 'installed_applications.json')
        self.assertTrue(os.path.isfile(full_path))
        json_data = json.load(open(full_path, "r"))
        print ("json ="), json_data
        apps = json_data
        self.assertIsNotNone(apps)
        self.assertIn('foo', apps) 

    def test_uninstalling_an_application(self):
        self._test_object.install('foo')

        self._test_object.uninstall('foo')

        self.assertNotIn('foo', self._test_object.installed_applications())
        
    def _make_file(self, dirname, filename, content = 'Testing'):
        f = open(os.path.join(dirname, filename), 'w')
        f.write(content)
        f.close()
