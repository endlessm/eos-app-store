from subprocess import PIPE, Popen, call
from shutil import copyfile
from eos_log import log

class OsUtil(object):
    VERSION_COMMAND = ["bash", "-c", "dpkg -s eos-app-store | grep ^Version: | awk \'{print $2}\'"] #| "
    
    def execute(self, cmd_args):
        p = Popen(cmd_args, stdout=PIPE)
        output = p.communicate()
        if p.returncode != 0:
            raise Exception(output[1])
        return output[0].strip()
    
    def execute_async(self, cmd_args):
        call(" ".join(cmd_args) + '&', shell=True)
        
    def copy(self, source, destination):
        if source is not destination:
            copyfile(source, destination)
    
    def get_version(self):
        try:
            return self.execute(self.VERSION_COMMAND)
        except Exception as e:
            log.error("An error occurred trying to read the version", e)
        return None
