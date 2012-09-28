
class AllSettingsPresenter():
    def __init__(self, view, model):
        view.set_current_version(model.get_current_version())

        view.display()
