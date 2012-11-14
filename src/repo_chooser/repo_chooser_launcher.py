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
