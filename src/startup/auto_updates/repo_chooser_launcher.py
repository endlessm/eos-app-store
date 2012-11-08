import gtk
from gtk import gdk #@UnusedImport
from subprocess import Popen

from update_manager import UpdateManager

# TODO test me
class RepoChooserLauncher(object):
    def __init__(self, update_manager=UpdateManager()):
        self._dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, "Welcome to the EndlessOS installer.")
        self._message = "Would you like to begin the Endless OS {env} update now?"
        self._dialog.format_secondary_text(self._message.format(env=""))
        self._dialog.set_position(gtk.WIN_POS_CENTER)
        self._dialog.set_modal(True)
        
        # TODO internationalize
        self._dialog.set_title("EndlessOS Installer")
        
        self._dialog.set_wmclass("eos-dialog", "Eos-dialog")
        self._dialog.connect("key_press_event", self._key_press_handler)
        
        self._env_mgr = EnvironmentManager()
        self._update_manager = update_manager 
        
        self._repo_def = self._env_mgr.find_repo(None)
        
    def launch(self):
        response = self._dialog.run()
        self._dialog.destroy()
        
        if response == gtk.RESPONSE_YES:
            self._update_manager.update_os()
            
    def _update_repo(self, repo_def):
        self._repo_def = repo_def
        self._dialog.format_secondary_text(self._message.format(env=self._repo_def.display))

    def _key_press_handler(self, widget, event):
        if event.state & gdk.CONTROL_MASK:
            if event.state & gdk.SHIFT_MASK:
                if gdk.keyval_name(event.keyval).lower() == "e": #@UndefinedVariable
                    repo_chooser = RepoChooser(self._dialog)
                    repo_chooser.get_repo(self._update_repo)

class EosInstallLauncher(object):
    def execute(self, repo_def):
        process = Popen(self._apply_template(repo_def), shell=True)
        
    def _apply_template(self, repo_def):
        template = "/bin/bash -c  'wget -q -O- {url} > /tmp/endless-installer.sh && bash /tmp/endless-installer.sh {repourl}'"
        return template.format(url=repo_def.installer_url, repourl=repo_def.repo_url)

class RepoChooser(object):
    def __init__(self, parent=None):
        self._repo_chooser = gtk.Dialog("Choose Repository", parent,  gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self._repo_chooser.set_wmclass("eos-dialog", "Eos-dialog")
        self._repo_chooser.set_default_response(gtk.RESPONSE_ACCEPT)
  
        label = gtk.Label("Password:")
        self._entry = gtk.Entry()
        self._entry.set_activates_default(True)
        self._entry.set_visibility(False)
        
        hbox = gtk.HBox(False, 2)
        hbox.pack_start(label)
        hbox.pack_end(self._entry)
        self._repo_chooser.vbox.pack_start(hbox)
        self._repo_chooser.show_all()
        
    def get_repo(self, callback):
        response = self._repo_chooser.run()
        
        env_mgr = EnvironmentManager()
        if response == gtk.RESPONSE_ACCEPT:
            callback(env_mgr.find_repo(self._entry.get_text()))
        
        self._repo_chooser.destroy()
        
class RepoDef(object):
    def __init__(self, display, installer_url, repo_url):
        self.display = display
        self.installer_url = installer_url
        self.repo_url = repo_url

class EnvironmentManager(object):
    DEFAULT_KEY = "prod"
    DEMO_KEY = "demo"
    DEV_KEY = "dev"
    CODEV_KEY = "codev"
    APT_TESTING_KEY = "apttesting"
       
    PROD_PASS = "production"
    DEMO_PASS = "demonstration"
    DEV_PASS = "development"
    CODEV_PASS = "codevelopment"
    APT_TESTING_PASS = "apttesting"
    
    REPOS = { 
                PROD_PASS : DEFAULT_KEY,
                DEMO_PASS : DEMO_KEY,
                DEV_PASS : DEV_KEY,
                CODEV_PASS : CODEV_KEY,
                APT_TESTING_PASS : APT_TESTING_KEY,
        }

    DATA = {
                DEFAULT_KEY : RepoDef("", "http://apt.endlessm.com/updates/674078905c57ea21b9eb6fd8f45f5b5b9a49f912/installer.sh", "apt.endlessm.com/updates/25af78cc1e54ca5bca7e1dfe980d5a251930a432"),
                DEMO_KEY : RepoDef("DEMO ", "http://apt.endlessm.com/demo/674078905c57ea21b9eb6fd8f45f5b5b9a49f912/installer.sh", "apt.endlessm.com/demo/25af78cc1e54ca5bca7e1dfe980d5a251930a432"),
                CODEV_KEY : RepoDef("CO-DEV ", "http://em-codev-build1/installer.sh", "em-codev-build1/repository"),
                DEV_KEY : RepoDef("DEV ", "http://em-vm-build/installer.sh", "em-vm-build/repository"),
                APT_TESTING_KEY : RepoDef("APT TESTING ", "http://apt.endlessm.com/apt_testing/674078905c57ea21b9eb6fd8f45f5b5b9a49f912/installer.sh", "apt.endlessm.com/apt_testing/25af78cc1e54ca5bca7e1dfe980d5a251930a432")
            }
    
    def find_repo(self, password):
        if password and password in self.REPOS:
            key = self.REPOS[password]
            return self.DATA[key]
        return self.DATA[self.DEFAULT_KEY]           
