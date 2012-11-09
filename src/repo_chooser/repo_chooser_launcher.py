from repo_chooser_presenter import RepoChooserPresenter
from repo_chooser_view import RepoChooserView
from repo_chooser_model import RepoChooserModel

class RepoChooserLauncher(object):
    def launch(self):
        RepoChooserPresenter(RepoChooserView(), RepoChooserModel())

if __name__ == "__main__":
    RepoChooserLauncher().launch()
    import gtk
    gtk.main()

#    def __init__(self)):
#        self._dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, "Welcome to the EndlessOS installer.")
#        self._message = "Would you like to begin the Endless OS {env} update now?"
#        self._dialog.format_secondary_text(self._message.format(env=""))
#        self._dialog.set_position(gtk.WIN_POS_CENTER)
#        self._dialog.set_modal(True)
#        
#        # TODO internationalize
#        self._dialog.set_title("EndlessOS Installer")
#        
#        self._dialog.set_wmclass("eos-dialog", "Eos-dialog")
#        self._dialog.connect("key_press_event", self._key_press_handler)
#        
#        self._env_mgr = EnvironmentManager()
#        self._update_manager = update_manager 
#        
#        self._repo_def = self._env_mgr.find_repo(None)
#        
#    def launch(self):
#        response = self._dialog.run()
#        self._dialog.destroy()
#        
#        if response == gtk.RESPONSE_YES:
#            self._update_manager.update_os()
#            
#    def _update_repo(self, repo_def):
#        self._repo_def = repo_def
#        self._dialog.format_secondary_text(self._message.format(env=self._repo_def.display))
#
#    def _key_press_handler(self, widget, event):
#        if event.state & gdk.CONTROL_MASK:
#            if event.state & gdk.SHIFT_MASK:
#                if gdk.keyval_name(event.keyval).lower() == "e": #@UndefinedVariable
#                    repo_chooser = RepoChooser(self._dialog)
#                    repo_chooser.get_repo(self._update_repo)
#
