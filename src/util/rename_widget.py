from gi.repository import Gtk
from eos_widgets.abstract_notifier import AbstractNotifier
from rename_widget_view import RenameWidgetView
from rename_widget_model import RenameWidgetModel
from rename_widget_presenter import RenameWidgetPresenter

class RenameWidget():

    def __init__(self, x, y, caller, caller_width):
        RenameWidgetPresenter(RenameWidgetView(x, y, caller_width), RenameWidgetModel(caller))

