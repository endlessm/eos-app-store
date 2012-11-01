
from osapps.web_connection import WebConnection

class InstallScriptExecutor():
    def __init__(self, web_connection=WebConnection()):
        self._web_connection = web_connection
        
    def execute_preinstall_script(self):
        pass

    def execute_postinstall_script(self):
        pass
