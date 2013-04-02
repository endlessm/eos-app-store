import unittest
import tempfile
import shutil
import os
from mock import Mock, call

from startup.windows_migration_tasks import WindowsMigrationTasks

class WindowsMigrationTasksTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_home_path_provider = Mock()
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
        self._make_windows_xp(num_users=2)
        users = self._test_object.get_windows_users(self._src_dir)
        self.assertEquals(2, len(users))
        self.assertEquals(0, users.index('WindowsUser1'))
        self.assertEquals(1, users.index('WindowsUser2'))

    def test_get_win_7_users(self):
        self._make_windows_7(num_users=2)
        users = self._test_object.get_windows_users(self._src_dir)
        self.assertEquals(2, len(users))
        self.assertEquals(0, users.index('WindowsUser1'))
        self.assertEquals(1, users.index('WindowsUser2'))

    def test_import_user_win_xp(self):
        self._make_windows_xp()
        self._test_object._create_link = Mock()
        self._test_object.pictures_dir = Mock(return_value='/home/user/pictures')
        self._test_object.music_dir = Mock(return_value='/home/user/music')
        self._test_object.videos_dir = Mock(return_value='/home/user/videos')
        self._test_object.documents_dir = Mock(return_value='/home/user/docs')
        self._test_object.import_user(self._src_dir, 'WindowsUser1', 'LinkName')
        calls = []
        calls.append(call(os.path.join(self._src_dir, 'Documents and Settings/WindowsUser1/My Documents'), '/home/user/docs/LinkName'))
        calls.append(call(os.path.join(self._src_dir, 'Documents and Settings/WindowsUser1/My Documents/My Pictures'), '/home/user/pictures/LinkName'))
        calls.append(call(os.path.join(self._src_dir, 'Documents and Settings/WindowsUser1/My Documents/My Music'), '/home/user/music/LinkName'))
        calls.append(call(os.path.join(self._src_dir, 'Documents and Settings/WindowsUser1/My Documents/My Videos'), '/home/user/videos/LinkName'))
        self._test_object._create_link.assert_has_calls(calls, any_order=True)

    def test_import_user_win_7(self):
        self._make_windows_7()
        self._test_object._create_link = Mock()
        self._test_object.pictures_dir = Mock(return_value='/home/user/pictures')
        self._test_object.music_dir = Mock(return_value='/home/user/music')
        self._test_object.videos_dir = Mock(return_value='/home/user/videos')
        self._test_object.documents_dir = Mock(return_value='/home/user/docs')
        self._test_object.import_user(self._src_dir, 'WindowsUser1', 'LinkName')
        calls = []
        calls.append(call(os.path.join(self._src_dir, 'Users/WindowsUser1/Documents'), '/home/user/docs/LinkName'))
        calls.append(call(os.path.join(self._src_dir, 'Users/WindowsUser1/Pictures'), '/home/user/pictures/LinkName'))
        calls.append(call(os.path.join(self._src_dir, 'Users/WindowsUser1/Music'), '/home/user/music/LinkName'))
        calls.append(call(os.path.join(self._src_dir, 'Users/WindowsUser1/Videos'), '/home/user/videos/LinkName'))
        self._test_object._create_link.assert_has_calls(calls, any_order=True)
        
    def test_import_mounted_directory_win_xp_single_user(self):
        self._make_windows_xp()
        self._test_object.import_user = Mock()
        self._test_object.import_mounted_directory(self._src_dir)
        # For a single user import, the generic name of 'Windows' is used instead of the real user name
        self._test_object.import_user.assert_called_once_with(self._src_dir, 'WindowsUser1', 'Windows')

    def test_import_mounted_directory_win_7_single_user(self):
        self._make_windows_7()
        self._test_object.import_user = Mock()
        self._test_object.import_mounted_directory(self._src_dir)
        # For a single user import, the generic name of 'Windows' is used instead of the real user name
        self._test_object.import_user.assert_called_once_with(self._src_dir, 'WindowsUser1', 'Windows')

    def test_import_mounted_directory_win_xp_multiple_users(self):
        self._make_windows_xp(num_users=2)
        self._test_object.import_user = Mock()
        self._test_object.import_mounted_directory(self._src_dir)
        calls = []
        calls.append(call(self._src_dir, 'WindowsUser1', 'WindowsUser1'))
        calls.append(call(self._src_dir, 'WindowsUser2', 'WindowsUser2'))
        self._test_object.import_user.assert_has_calls(calls, any_order=True)

    def test_import_mounted_directory_win_7_multiple_users(self):
        self._make_windows_7(num_users=2)
        self._test_object.import_user = Mock()
        self._test_object.import_mounted_directory(self._src_dir)
        calls = []
        calls.append(call(self._src_dir, 'WindowsUser1', 'WindowsUser1'))
        calls.append(call(self._src_dir, 'WindowsUser2', 'WindowsUser2'))
        self._test_object.import_user.assert_has_calls(calls, any_order=True)

    def test_creating_links(self):
        self._make_file(self._src_dir, 'bar')
        source = os.path.join(self._src_dir, 'bar')
        link = os.path.join(self._dst_dir, 'foo')
        self._test_object._create_link(source, link)
        self.assertTrue(os.access(link, os.R_OK))
        self.assertTrue(os.path.islink(link))
        self.assertEqual(source, os.readlink(link))

    def test_creating_links_preserves_existing(self):
        self._make_file(self._src_dir, 'bar')
        os.symlink(os.path.join(self._src_dir, 'bar'), os.path.join(self._dst_dir, 'foo'))
        
        source = os.path.join(self._src_dir, 'bar')
        link = os.path.join(self._dst_dir, 'foo')
        self._test_object._create_link(source, link)
        self.assertTrue(os.access(link, os.R_OK))
        self.assertTrue(os.path.islink(link))
        self.assertEqual(source, os.readlink(link))
    
    def test_get_users_pictures_directory(self):
        self._mock_home_path_provider.get_pictures_directory = Mock(return_value="something")
        
        self.assertEqual('something', self._test_object.pictures_dir())
        
        self.assertTrue(self._mock_home_path_provider.get_pictures_directory.called)

    def test_get_users_videos_directory(self):
        self._mock_home_path_provider.get_videos_directory = Mock(return_value="something")
        
        self.assertEqual('something', self._test_object.videos_dir())
        
        self.assertTrue(self._mock_home_path_provider.get_videos_directory.called)

    def test_get_users_music_directory(self):
        self._mock_home_path_provider.get_music_directory = Mock(return_value="something")
        
        self.assertEqual('something', self._test_object.music_dir())
        
        self.assertTrue(self._mock_home_path_provider.get_music_directory.called)

    def test_get_users_documents_directory(self):
        self._mock_home_path_provider.get_documents_directory = Mock(return_value="something")
        
        self.assertEqual('something', self._test_object.documents_dir())
        
        self.assertTrue(self._mock_home_path_provider.get_documents_directory.called)

    def _make_windows_xp(self, num_users=1):
        documents_dir = os.path.join(self._src_dir, 'Documents and Settings')
        os.mkdir(documents_dir)
        self._make_windows_xp_users_dir(documents_dir, num_users)
    
    def _make_windows_7(self, num_users=1):
        documents_dir = os.path.join(self._src_dir, 'Users')
        os.mkdir(documents_dir)
        self._make_windows_7_users_dir(documents_dir, num_users)
    
    def _make_windows_xp_users_dir(self, documents_dir, num_users):
        # Note: the default names should be excluded by the logic under test
        user_names = ['All Users', 'Default User', 'LocalService', 'NetworkService']
        for user_num in range(1, num_users + 1):
            user_names.append('WindowsUser' + str(user_num))
        for user_name in user_names:
            user_dir = os.path.join(documents_dir, user_name)
            os.mkdir(user_dir)
            self._make_windows_xp_home_dir(user_dir)

    def _make_windows_7_users_dir(self, documents_dir, num_users):
        # Note: the default names should be excluded by the logic under test
        user_names = ['All Users', 'Default', 'Default User', 'Public', 'Todos os Usu\xc3\xa1rios', 'Usu\xc3\xa1rio Padr\xc3\xa3o']
        for user_num in range(1, num_users + 1):
            user_names.append('WindowsUser' + str(user_num))
        for user_name in user_names:
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
    
