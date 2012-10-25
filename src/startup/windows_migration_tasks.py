import os
from subprocess import Popen, PIPE

class WindowsMigrationTasks:
    USER_PATH = '/home/endlessm'
    MOUNT_POINT = '/eos-mnt'
    
    def __init__(self):
        # For now, support only English and Portuguese
        # Note: 'Documents and Settings' is not internationalized on Portuguese Win XP
        self._documents_and_settings = ['Documents and Settings']
        self._users = ['Users', 'Usu\xc3\xa1rios']
        self._xp_pic_dirs = ['My Pictures', 'Minhas Imagens']
        self._xp_video_dirs = ['My Videos', 'Meus V\xc3\xaddeos']
        self._xp_music_dirs = ['My Music', 'Minhas M\xc3\xbasicas']
        self._xp_docs_dirs = ['My Documents', 'Meus Documentos']
        self._w7_docs_dirs = ['Documents', 'Documentos']
        self._w7_pic_dirs = ['Pictures', 'Imagens']
        self._w7_video_dirs = ['Videos', 'V\xc3\xaddeos']
        self._w7_music_dirs = ['Music', 'M\xc3\xbasicas']
    
    def execute(self):
        for directory in os.listdir(self.MOUNT_POINT):
            full_path = os.path.join(self.MOUNT_POINT, directory)
            if os.path.isdir(full_path):
                self.import_mounted_directory(full_path)
    
    def import_mounted_directory(self, mount_point):
        for user in self.get_windows_users(mount_point):
            self.import_user(mount_point, user)

    def is_windows(self, mount_point):
        return self.is_windows_7(mount_point) or self.is_windows_xp(mount_point) 
    
    def is_windows_xp(self, mount_point):
        # different language versions of the "D+S" directory name
        return self._test_dirs_exist(mount_point, self._documents_and_settings)
        
    def is_windows_7(self, mount_point):
        # different language versions of the "User" directory name
        return self._test_dirs_exist(mount_point, self._users)

    def get_windows_users(self, mount_point):
        paths_to_user_home = []
        for directory in self._documents_and_settings:
            path = os.path.join(mount_point, directory)
            self._add_all_subdirs(paths_to_user_home, path)

        for directory in self._users:
            path = os.path.join(mount_point, directory)
            self._add_all_subdirs(paths_to_user_home, path)
        
        paths_to_user_home.sort()
        return paths_to_user_home

    def import_user(self, mount_point, user):
        if (self.is_windows_7(mount_point)):
            for directory in self._users:
                home_path = os.path.join(mount_point, directory)
                path = os.path.join(home_path, user)
                self._link_directory(user, path, self._w7_docs_dirs, self.documents_dir())
                self._link_directory(user, path, self._w7_pic_dirs, self.pictures_dir())
                self._link_directory(user, path, self._w7_music_dirs, self.music_dir())
                self._link_directory(user, path, self._w7_video_dirs, self.videos_dir())
        elif (self.is_windows_xp(mount_point)):
            for directory in self._documents_and_settings:
                home_path = os.path.join(mount_point, directory)
                path = os.path.join(home_path, user)
                for doc_dir in self._xp_docs_dirs:
                    docs_path = os.path.join(path, doc_dir)
                    if os.path.isdir(docs_path):
                        dest = self.documents_dir()
                        self._create_link(user, docs_path, dest)
                        self._link_directory(user, docs_path, self._xp_pic_dirs, self.pictures_dir())
                        self._link_directory(user, docs_path, self._xp_music_dirs, self.music_dir())
                        self._link_directory(user, docs_path, self._xp_video_dirs, self.videos_dir())
    
    def pictures_dir(self):
        return os.path.join(self.USER_PATH, self._localize_directory('Pictures'))
    
    def videos_dir(self):
        return os.path.join(self.USER_PATH, self._localize_directory('Videos'))
    
    def documents_dir(self):
        return os.path.join(self.USER_PATH, self._localize_directory('Documents'))
    
    def music_dir(self):
        return os.path.join(self.USER_PATH, self._localize_directory('Music'))
    
    def _create_link(self, link_name, destination, parent_dir):
        link = os.path.join(parent_dir, link_name)
        if not os.path.islink(link):
            os.symlink(destination, link)
    
    def _add_all_subdirs(self, list_of_users, parent):
        if os.path.isdir(parent):
            for directory in os.listdir(parent):
                if os.path.isdir(os.path.join(parent, directory)):
                    list_of_users.append(directory)
    
    def _test_dirs_exist(self, parent_dir, dirs):
        for directory in dirs:
            if os.path.isdir(os.path.join(parent_dir, directory)):
                return True
        return False

    def _link_directory(self, user, parent, source_dirs_list, target_dir):
        for source_dir in source_dirs_list:
            path = os.path.join(parent, source_dir)
            if os.path.isdir(path):
                self._create_link(user, path, target_dir)

    def _add_to_fstab(self, device, mount_point):
        mgr = FstabManager(self.FSTAB_PATH)
        mgr.mount_device(device, mount_point)
        
    def _localize_directory(self, directory):
        localized_name = self._execute(["gettext", "-d", "xdg-user-dirs", directory])
        return localized_name

    def _execute(self, cmd_args):
        p = Popen(cmd_args, stdout=PIPE)
        output = p.communicate()
        if p.returncode != 0:
            raise Exception(output[1])
        return output[0].strip()
    

if __name__ == '__main__':
    WindowsMigrationTasks().execute()
