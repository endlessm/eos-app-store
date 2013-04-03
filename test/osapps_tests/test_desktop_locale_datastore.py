from unittest import TestCase
import os
import json
from mock import MagicMock, Mock
from osapps.os_util import OsUtil
from osapps.desktop_locale_datastore import DesktopLocaleDatastore


# TODO where are the tests for non-default locales?

class DesktopLocaleDatastoreTest(TestCase):
	_filename = "/tmp/desktop.en_US"
	_filename2 = "/tmp/desktop.pt_BR"
	_shortcut_file = "/tmp/desktop.json"
	_dir = "/tmp/"
	_default_prefix="desktop."

	def setUp(self):
		OsUtil().execute(["rm", "-f", self._filename])
		file_data = [
  						{"key":"browser", "icon":"browser.png", "name":"Browser"}
  						,{"key":"photos", "icon":"photos.png", "name":"Photos"}
  						,{"key":"", "icon":"folder.png", "name":"News", "children":
							[
								{"key":"browser", "icon":"msn.png", "name":"MSN", "params":["http://msn.com"]}
								,{"key":"browser", "icon":"yahoo.png", "name":"Yahoo", "params":["http://yahoo.com"]}
							]
						}

					]

		file_data2 = [
  						{"key":"browser", "icon":"browser.png", "name":"Browser"}
					]

		file_content = json.dumps(file_data)
		with open(self._filename, "w") as f:
			f.write(file_content)

		file_content2 = json.dumps(file_data2)
		with open(self._filename2, "w") as f:
			f.write(file_content2)

		self._mock_locale_utils = Mock()
		self._mock_locale_utils.get_locale = Mock(return_value="en_US")
		self._mock_locale_utils.get_default_locale = Mock(return_value="en_US")

		self._test_object = DesktopLocaleDatastore(self._shortcut_file, self._dir, self._mock_locale_utils)

	def tearDown(self):
		OsUtil().execute(["rm", "-f", self._filename])
		OsUtil().execute(["rm", "-f", self._filename2])
		OsUtil().execute(["rm", "-f", self._shortcut_file])

	def test_app_load(self):
		shortcuts = self._test_object.get_all_shortcuts()

		shortcut = shortcuts[0]

		self.assertEqual("browser", shortcut.key())
		self.assertEqual("browser.png", shortcut.icon())
		self.assertEqual("Browser", shortcut.name())

		shortcut = shortcuts [2]
		self.assertEqual("News", shortcut.name())
		self.assertEqual(2, len(shortcut.children()))

		self.assertEqual("browser", shortcut.children()[0].key())
		self.assertEqual(["http://msn.com"], shortcut.children()[0].params())

		self.assertEqual("browser", shortcut.children()[1].key())
		self.assertEqual("Yahoo", shortcut.children()[1].name())
		self.assertEqual(["http://yahoo.com"], shortcut.children()[1].params())

	def test_with_desktop_locale_that_is_not_the_default_one(self):
		OsUtil().execute(["rm", "-f", self._shortcut_file])
		self._mock_locale_utils.get_locale = MagicMock(return_value="pt_BR")
		self.assertFalse(os.path.exists(self._shortcut_file))
		self._test_object = DesktopLocaleDatastore(self._shortcut_file, self._dir, self._mock_locale_utils)

		shortcuts = self._test_object.get_all_shortcuts()
		self.assertTrue(os.path.exists(self._shortcut_file))

		self.assertEquals(1, len(shortcuts))

		shortcut = shortcuts[0]

		self.assertEqual("browser", shortcut.key())
		self.assertEqual("browser.png", shortcut.icon())
		self.assertEqual("Browser", shortcut.name())

	def test_with_desktop_locale_that_is_not_available(self):
		OsUtil().execute(["rm", "-f", self._shortcut_file])
		self._mock_locale_utils.get_locale = MagicMock(return_value="en_GB")
		self.assertFalse(os.path.exists(self._shortcut_file))
		self._test_object = DesktopLocaleDatastore(self._shortcut_file, self._dir, self._mock_locale_utils)

		shortcuts = self._test_object.get_all_shortcuts()
		self.assertTrue(os.path.exists(self._shortcut_file))

		self.assertEquals(3, len(shortcuts))

		shortcut = shortcuts[0]

		self.assertEqual("browser", shortcut.key())
		self.assertEqual("browser.png", shortcut.icon())
		self.assertEqual("Browser", shortcut.name())


	def test_with_default_desktop_locale(self):
		OsUtil().execute(["rm", "-f", self._shortcut_file])
		self.assertFalse(os.path.exists(self._shortcut_file))
		self._test_object = DesktopLocaleDatastore(self._shortcut_file, self._dir, self._mock_locale_utils)

		shortcuts = self._test_object.get_all_shortcuts()
		self.assertTrue(os.path.exists(self._shortcut_file))

		shortcut = shortcuts[0]

		self.assertEqual("browser", shortcut.key())
		self.assertEqual("browser.png", shortcut.icon())
		self.assertEqual("Browser", shortcut.name())

	def test_add_shortcut(self):
		new_shortcut_name = 'Blah'
		current_shortcuts = self._test_object.get_all_shortcuts()
		shortcut = current_shortcuts[0]
		shortcut._name = new_shortcut_name
		self._test_object.add_shortcut(shortcut)
		updated_shortcuts = self._test_object.get_all_shortcuts()
		self.assertEqual(True, new_shortcut_name in [s.name() for s in updated_shortcuts])
		self.assertEqual(len(updated_shortcuts), len(current_shortcuts) + 1)

