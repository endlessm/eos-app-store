
class FileSynchronizer():
    def __init__(self):
        pass

    def files_to_download(self, local_file_list, remote_file_list):
        all_remote = remote_file_list.strip().split("\n")

        for local_file in local_file_list.strip().split("\n"):
            if local_file in all_remote:
                all_remote.remove(local_file)

        for remote in all_remote:
            if remote == '':
                all_remote.remove(remote)

        return all_remote
        
