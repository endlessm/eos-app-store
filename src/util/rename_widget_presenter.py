from rename_widget_constants import RenameWidgetConstants

class RenameWidgetPresenter():
    def __init__(self, view, model):
        view.add_listener(RenameWidgetConstants.ESCAPE_PRESSED, view.close_window)
        view.add_listener(RenameWidgetConstants.RETURN_PRESSED, lambda: self._save_new_name(view, model))

        view.set_original_name(model.get_original_name())
        view.resize_window()
        view.show_window()

    def _save_new_name(self, view, model):
        model.save(view.get_new_name())
        view.close_window()
