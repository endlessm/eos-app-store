## {{{ http://code.activestate.com/recipes/546512/ (r1)
import commands
import os
from util import file_util

class singleinstance(object):
    '''
    singleinstance - based on Windows version by Dragan Jovelic this is a Linux
                     version that accomplishes the same task: make sure that
                     only a single instance of an application is running.
    '''
                        
    def __init__(self):
        '''
        pidPath - full path/filename where pid for running application is to be
                  stored.  Often this is ./var/<pgmname>.pid
        '''
        self.lasterror = False
        
        self.pidPath = file_util.get_file_path_in_config_dir("endless_os_deskt_widget.pid")
        self.pid = None
        
        if os.path.exists(self.pidPath):
            self.pid = open(self.pidPath, 'r').read().strip()
            pidRunning = commands.getoutput('ls /proc | grep %s' % self.pid)
            if pidRunning:
                self.lasterror = True

        if not self.lasterror:
            fp = open(self.pidPath, 'w')
            fp.write(str(os.getpid()))
            fp.close()

    def alreadyrunning(self):
        return self.lasterror

    def __del__(self):
        if not self.lasterror:
            os.unlink(self.pidPath)

    def instance_already_running(self):
        return self.alreadyrunning()
            
    def existing_pid(self):
        return self.pid        