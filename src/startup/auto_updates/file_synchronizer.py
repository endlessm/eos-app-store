import re
from eos_log import log

class FileSynchronizer():
    def __init__(self):
        pass

    def files_to_download(self, local_file_list, remote_file_content):
        remote_file_list = remote_file_content.splitlines()
        log.info("length of remote file list: %d" % len(remote_file_list))
        log.info("length of local files: %d" % len(local_file_list))
        
        remote_tuples = []
        for remote_entry in remote_file_list:
            entry_tuple = re.findall("^\s*(\S+)\s+(\S+)\s*$", remote_entry)[0]
            remote_tuples.append((entry_tuple[1].strip(), entry_tuple[0].strip()))

        return [remote_tuple for remote_tuple in remote_tuples if remote_tuple[0] not in local_file_list]
        
