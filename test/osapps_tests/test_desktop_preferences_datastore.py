import os

from unittest import TestCase
from mock import Mock, call  #@UnresolvedImport

from osapps.desktop_preferences_datastore import DesktopPreferencesDatastore
from osapps.os_util import OsUtil
from eos_util.image import Image

class DesktopPreferencesDatastoreTest(TestCase):
	def setUp(self):
		self._preferences_file = os.path.join(DesktopPreferencesDatastore.PREF_DIRNAME,
											  DesktopPreferencesDatastore.PREF_FILENAME
											)
		try:
			OsUtil().execute(["rm", "-f", self._preferences_file])
		except:
			pass #Could not erase preferences file
		
		def get_image(filename):
			return filename + "_image"
		
		Image.from_path = Mock(side_effect=get_image)

		DesktopPreferencesDatastore._file_exists = Mock(return_value=True)
		DesktopPreferencesDatastore._instance = None
		
	def tearDown(self):
		try:
			OsUtil().execute(["rm", "-f", self._preferences_file])
		except:
			pass #Could not erase preferences file
		
	def test_get_instance_returns_existing_instance_when_one_exists(self):
		instance1 = DesktopPreferencesDatastore.get_instance()
		self.assertIsNotNone(instance1)
		
		instance2 = DesktopPreferencesDatastore.get_instance()
		self.assertEqual(instance1, instance2)
		
		self.assertEquals(type(instance1), DesktopPreferencesDatastore)
	
	def test_get_default_background_return_default_image_location(self):
		_test_object = DesktopPreferencesDatastore.get_instance()
		_actual_background = _test_object.get_default_background()
		self.assertTrue(DesktopPreferencesDatastore.DEFAULT_BG_LOCATION, _actual_background)
		
	def test_get_background_image_returns_default_image(self):
		mock_os_util = Mock()
		_test_object = DesktopPreferencesDatastore.get_instance(mock_os_util)
		
		_background_image = _test_object.get_background_image()
		
		self.assertEquals(_test_object.DEFAULT_BG_LOCATION + "_image", _background_image)
		
	def test_saving_a_new_background_copies_the_file(self):
		mock_os_util = Mock()
		_test_object = DesktopPreferencesDatastore.get_instance(mock_os_util)
		
		new_background = 'new_background'
		
		_test_object.set_background(new_background)
		
		expected_bg_location2 = os.path.join(_test_object.PREF_DIRNAME, new_background)

		self.assertEquals(expected_bg_location2 + "_image", _test_object.get_background_image())
		mock_os_util.copy.assert_has_calls([call(new_background, expected_bg_location2)])
	
	def test_settings_are_persisted(self):
		_test_object = DesktopPreferencesDatastore.get_instance()

		new_background = '/tmp/new_background2'
		expected_content = "asdffasdfdasfasdf"
		open(new_background, "w").write(expected_content)

		_test_object.set_background(new_background)
		
		DesktopPreferencesDatastore._instance = None
		_test_object = DesktopPreferencesDatastore.get_instance()
		
		expected_bg_location = os.path.join(_test_object.PREF_DIRNAME, os.path.basename(new_background))
		
		_background_image = _test_object.get_background_image()
		self.assertEquals(expected_bg_location + "_image", _background_image)
		
	def test_when_settings_are_corrupt_use_default_image(self):
		_test_object = DesktopPreferencesDatastore.get_instance()

		new_background = '/tmp/new_background2'
		expected_content = "asdffasdfdasfasdf"
		open(new_background, "w").write(expected_content)

		_test_object.set_background(new_background)
		
		OsUtil().execute(["rm", "-f", new_background])
		
		DesktopPreferencesDatastore._file_exists = Mock(return_value=False)
		
		DesktopPreferencesDatastore._instance = None
		_test_object = DesktopPreferencesDatastore.get_instance()
		
		_background_image = _test_object.get_background_image()
		self.assertEquals(DesktopPreferencesDatastore.DEFAULT_BG_LOCATION + "_image", _background_image)		

	def test_get_scaled_background_image(self):
		mock_os_util = Mock()
		_test_object = DesktopPreferencesDatastore.get_instance(mock_os_util)
		width = Mock()
		height = Mock()
		mock_image = Mock()
		mock_image.copy = Mock(return_value=mock_image)
		mock_image.scale_to_best_fit = Mock(return_value=mock_image)
		def get_image(filename):
			return mock_image
		Image.from_path = Mock(side_effect=get_image)
		Image.copy = Mock()
		
		_background_image = _test_object.get_scaled_background_image(width, height)
		
		mock_image.copy.assert_called_once_with()
		mock_image.scale_to_best_fit.assert_called_once_with(width, height)
		self.assertEquals(mock_image, _background_image)
		