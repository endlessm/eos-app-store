import unittest
import tempfile
import shutil
import os
from mock import Mock, call

from startup.windows_migration_tasks import WindowsMigrationTasks

class WindowsMigrationTasksTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_home_path_provider = Mock()
        self._mock_home_path_provider.get_user_directory = Mock(return_value="")
        self._test_object = WindowsMigrationTasks(self._mock_home_path_provider)
        # Create temporary directories
        self._src_dir = tempfile.mkdtemp()
        self._dst_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # Remove the temporary directories
        shutil.rmtree(self._src_dir)
        shutil.rmtree(self._dst_dir)

    def test_is_windows_given_xp(self):
        self._make_windows_xp()
        self.assertTrue(self._test_object.is_windows(self._src_dir))
        
    def test_is_windows_given_7(self):
        self._make_windows_7()
        self.assertTrue(self._test_object.is_windows(self._src_dir))
        
    def test_is_source_system_win_xp(self):
        self._make_windows_xp()
        self.assertTrue(self._test_object.is_windows_xp(self._src_dir))

    def test_win_xp_documents_and_settings_is_dir(self):
        self._make_file(self._src_dir, 'Documents and Settings')
        self.assertFalse(self._test_object.is_windows_xp(self._src_dir))

    def test_is_source_system_win_7(self):
        self._make_windows_7()
        self.assertTrue(self._test_object.is_windows_7(self._src_dir))

    def test_win_7_users_is_dir(self):
        self._make_file(self._src_dir, 'Users')
        self.assertFalse(self._test_object.is_windows_7(self._src_dir))

    def test_source_system_isnt_windows(self):
        self.assertFalse(self._test_object.is_windows_xp(self._src_dir))
        self.assertFalse(self._test_object.is_windows_7(self._src_dir))
        
    def test_get_win_xp_users(self):
        self._make_windows_xp()
        users = self._test_object.get_windows_users(self._src_dir)
        self.assertEquals(2, len(users))
        self.assertEquals(0, users.index('Another User'))
        self.assertEquals(1, users.index('WindowsUser'))

    def test_get_win_7_users(self):
        self._make_windows_7()
        users = self._test_object.get_windows_users(self._src_dir)
        self.assertEquals(2, len(users))
        self.assertEquals(0, users.index('Another User'))
        self.assertEquals(1, users.index('WindowsUser'))

    def test_import_win_xp_user(self):
        self._make_windows_xp()
        self._test_object._create_link = Mock()
        self._test_object.pictures_dir = Mock(return_value='/home/user/pictures')
        self._test_object.music_dir = Mock(return_value='/home/user/music')
        self._test_object.videos_dir = Mock(return_value='/home/user/videos')
        self._test_object.documents_dir = Mock(return_value='/home/user/docs')
        self._test_object.import_user(self._src_dir, 'WindowsUser')
        calls = []
        calls.append(call('WindowsUser', os.path.join(self._src_dir, 'Documents and Settings/WindowsUser/My Documents'), '/home/user/docs'))
        calls.append(call('WindowsUser', os.path.join(self._src_dir, 'Documents and Settings/WindowsUser/My Documents/My Pictures'), '/home/user/pictures'))
        calls.append(call('WindowsUser', os.path.join(self._src_dir, 'Documents and Settings/WindowsUser/My Documents/My Music'), '/home/user/music'))
        calls.append(call('WindowsUser', os.path.join(self._src_dir, 'Documents and Settings/WindowsUser/My Documents/My Videos'), '/home/user/videos'))
        self._test_object._create_link.assert_has_calls(calls, any_order=True)

    def test_import_win_7_user(self):
        self._make_windows_7()
        self._test_object._create_link = Mock()
        self._test_object.pictures_dir = Mock(return_value='/home/user/pictures')
        self._test_object.music_dir = Mock(return_value='/home/user/music')
        self._test_object.videos_dir = Mock(return_value='/home/user/videos')
        self._test_object.documents_dir = Mock(return_value='/home/user/docs')
        self._test_object.import_user(self._src_dir, 'WindowsUser')
        calls = []
        calls.append(call('WindowsUser', os.path.join(self._src_dir, 'Users/WindowsUser/Documents'), '/home/user/docs'))
        calls.append(call('WindowsUser', os.path.join(self._src_dir, 'Users/WindowsUser/Pictures'), '/home/user/pictures'))
        calls.append(call('WindowsUser', os.path.join(self._src_dir, 'Users/WindowsUser/Music'), '/home/user/music'))
        calls.append(call('WindowsUser', os.path.join(self._src_dir, 'Users/WindowsUser/Videos'), '/home/user/videos'))
        self._test_object._create_link.assert_has_calls(calls, any_order=True)
        
    def test_import_win_xp_multiple_users(self):
        self._make_windows_xp()
        self._test_object.import_user = Mock()
        self._test_object.import_mounted_directory(self._src_dir)
        calls = []
        calls.append(call(self._src_dir, 'WindowsUser'))
        calls.append(call(self._src_dir, 'Another User'))
        self._test_object.import_user.assert_has_calls(calls, any_order=True)

    def test_import_win_7_multiple_users(self):
        self._make_windows_7()
        self._test_object.import_user = Mock()
        self._test_object.import_mounted_directory(self._src_dir)
        calls = []
        calls.append(call(self._src_dir, 'WindowsUser'))
        calls.append(call(self._src_dir, 'Another User'))
        self._test_object.import_user.assert_has_calls(calls, any_order=True)

    def test_creating_links(self):
        self._make_file(self._src_dir, 'bar')
        target = os.path.join(self._src_dir, 'bar')
        expected = os.path.join(self._dst_dir, 'foo')
        self._test_object._create_link('foo', target, self._dst_dir)
        self.assertTrue(os.access(expected, os.R_OK))
        self.assertTrue(os.path.islink(expected))
        self.assertEqual(target, os.readlink(expected))

    def test_creating_links_preserves_existing(self):
        self._make_file(self._src_dir, 'bar')
        os.symlink(os.path.join(self._src_dir, 'bar'), os.path.join(self._dst_dir, 'foo'))
        
        target = os.path.join(self._src_dir, 'bar')
        expected = os.path.join(self._dst_dir, 'foo')
        self._test_object._create_link('foo', target, self._dst_dir)
        self.assertTrue(os.access(expected, os.R_OK))
        self.assertTrue(os.path.islink(expected))
        self.assertEqual(target, os.readlink(expected))
    
    def test_get_users_pictures_directory(self):
        self._mock_home_path_provider.get_user_directory = Mock(return_value="something")
        
        self.assertEqual('something', self._test_object.pictures_dir())
        
        self._mock_home_path_provider.get_user_directory.assert_called_once_with("Pictures")

    def test_get_users_videos_directory(self):
        self._mock_home_path_provider.get_user_directory = Mock(return_value="something")
        
        self.assertEqual('something', self._test_object.videos_dir())
        
        self._mock_home_path_provider.get_user_directory.assert_called_once_with("Videos")

    def test_get_users_music_directory(self):
        self._mock_home_path_provider.get_user_directory = Mock(return_value="something")
        
        self.assertEqual('something', self._test_object.music_dir())
        
        self._mock_home_path_provider.get_user_directory.assert_called_once_with("Music")

    def test_get_users_documents_directory(self):
        self._mock_home_path_provider.get_user_directory = Mock(return_value="something")
        
        self.assertEqual('something', self._test_object.documents_dir())
        
        self._mock_home_path_provider.get_user_directory.assert_called_once_with("Documents")

    def _make_windows_xp(self):
        documents_dir = os.path.join(self._src_dir, 'Documents and Settings')
        os.mkdir(documents_dir)
        self._make_windows_xp_users_dir(documents_dir)
    
    def _make_windows_7(self):
        documents_dir = os.path.join(self._src_dir, 'Users')
        os.mkdir(documents_dir)
        self._make_windows_7_users_dir(documents_dir)
    
    def _make_windows_xp_users_dir(self, documents_dir):
        # Note: all names other than the first two should be excluded by the logic under test
        for user_name in ['WindowsUser', 'Another User', 'All Users', 'Default User', 'LocalService', 'NetworkService']:
            user_dir = os.path.join(documents_dir, user_name)
            os.mkdir(user_dir)
            self._make_windows_xp_home_dir(user_dir)

    def _make_windows_7_users_dir(self, documents_dir):
        # Note: all names other than the first two should be excluded by the logic under test
        for user_name in ['WindowsUser', 'Another User', 'All Users', 'Default', 'Default User', 'Public', 'Todos os Usu\xc3\xa1rios', 'Usu\xc3\xa1rio Padr\xc3\xa3o']:
            user_dir = os.path.join(documents_dir, user_name)
            os.mkdir(user_dir)
            self._make_windows_7_home_dir(user_dir)
        
    def _make_windows_xp_home_dir(self, user_dir):
        docs_dir = os.path.join(user_dir, 'My Documents')
        os.mkdir(docs_dir)
        os.mkdir(os.path.join(docs_dir, 'My Music'))
        os.mkdir(os.path.join(docs_dir, 'My Pictures'))
        os.mkdir(os.path.join(docs_dir, 'My Videos'))
    
    def _make_windows_7_home_dir(self, user_dir):
        os.mkdir(os.path.join(user_dir, 'Documents'))
        os.mkdir(os.path.join(user_dir, 'Music'))
        os.mkdir(os.path.join(user_dir, 'Pictures'))
        os.mkdir(os.path.join(user_dir, 'Videos'))
    
    def _make_file(self, dirname, filename, content = 'Testing'):
        f = open(os.path.join(dirname, filename), 'w')
        f.write(content)
        f.close()
        
    def test_execution_will_crawl_all_directories_in_mount_point_and_import_all_children(self):
        self._test_object.import_mounted_directory = Mock()
        
        self._test_object.MOUNT_POINT = self._src_dir
        full_path1 = os.path.join(self._test_object.MOUNT_POINT, "dir1")
        full_path2 = os.path.join(self._test_object.MOUNT_POINT, "dir2")
        full_path3 = os.path.join(self._test_object.MOUNT_POINT, "file1")
        
        os.makedirs(full_path1)
        os.makedirs(full_path2)
        open(full_path3, "w").close()
        
        self._test_object.execute()
    
        for expected_call in [ call(full_path1), call(full_path2) ]:
            assert expected_call in self._test_object.import_mounted_directory.call_args_list
        self.assertEqual(2, self._test_object.import_mounted_directory.call_count)
    
    def test_execution_not_blow_up_if_theres_no_mount_directory(self):
        self._test_object.MOUNT_POINT = "monkeys"
        
        self._test_object.execute()
    
