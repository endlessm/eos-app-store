from unittest import TestCase
import json
from mock import MagicMock
from osapps.os_util import OsUtil
from osapps.app_datastore import AppDatastore

class AppDatastoreTest(TestCase):
	_filename = "/tmp/app_list.txt"
	
	def setUp(self):
		OsUtil().execute(["rm", "-f", self._filename])
		file_data = {
  						"photos":"eog.desktop"
    					,"text-editor":"gedit.desktop"
					}

		file_content = json.dumps(file_data)
		with open(self._filename, "w") as f:
			f.write(file_content)
		self._test_object = AppDatastore(self._filename)
#		self._test_object.get_all_apps()
		
	def tearDown(self):
		OsUtil().execute(["rm", "-f", self._filename])
		
	def test_app_load(self):
		app = self._test_object.get_app_by_key("photos")
		
		self.assertEqual("eog", app.executable())
		
		app = self._test_object.get_app_by_key(None)
		
		self.assertEqual(None, app)
		
		app = self._test_object.get_app_by_key("foo")
		
		self.assertEqual(None, app)

	def test_find_app_by_desktop(self):
		app = self._test_object.find_app_by_desktop("eog.desktop")
		
		self.assertEqual("eog", app.executable())
		
		app = self._test_object.find_app_by_desktop(None)
		
		self.assertEqual(None, app)
		
		app = self._test_object.find_app_by_desktop("foo.bar")
		
		self.assertEqual(None, app)
		
		
	