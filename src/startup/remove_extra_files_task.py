import os
from eos_log import log
import shutil

class RemoveExtraFilesTask:
    def __init__(self, os_util=os, sh_util=shutil):
        self._os_util = os_util
        self._sh_util = sh_util
        self.FILES_TO_REMOVE = [
                    "~/application.list",
                    "~/desktop.en_US",
                    "~/desktop.pt_BR",
                    "~/fluxbox-startup.log",
                ]
        
    def execute(self):
        for the_file in self.FILES_TO_REMOVE:
            try:
                print "removing ", the_file
                self._os_util.remove(self._os_util.path.expanduser(the_file))
            except Exception as e:
                log.error("An error ocurred while removing " + the_file, e)

       
