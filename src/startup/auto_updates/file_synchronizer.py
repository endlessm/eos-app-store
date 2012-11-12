import re
from eos_log import log

class FileSynchronizer():
    def __init__(self):
        pass

    def files_to_download(self, local_file_list, remote_file_list):
        log.info("size of list of local files: %d" % len(local_file_list))
        log.info("size of list of remote files: %d" % len(remote_file_list))
        
        remote_tuples = []
        for remote_entry in remote_file_list.splitlines():
            entry_tuple = re.findall("^\s*(\S+)\s+(\S+)\s*$", remote_entry)[0]
            remote_tuples.append((entry_tuple[1], entry_tuple[0]))

        for remote_tuple in remote_tuples:
            if remote_tuple[0] in local_file_list:
                remote_tuples.remove(remote_tuple)

        log.info("size of returned tuples: %d" % len(remote_tuples))
        return remote_tuples
        
