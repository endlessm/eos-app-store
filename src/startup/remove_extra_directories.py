import os
from eos_log import log
import shutil

class RemoveExtraDirectoriesTask:
    def __init__(self, os_util=os, sh_util=shutil):
        self._os_util = os_util
        self._sh_util = sh_util
        self.DIRECTORIES_TO_REMOVE = [
                    "~/Public",
                    "~/Templates"
                ]
        
    def execute(self):
        for directory in self.DIRECTORIES_TO_REMOVE:
            try:
                self._sh_util.rmtree(self._os_util.path.expanduser(directory))
            except Exception as e:
                log.error("An error ocurred while removing " + directory, e)

       
