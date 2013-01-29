import gtk
import gobject

from feedback.feedback_response_dialog_view import FeedbackResponseDialogView
from feedback.bugs_and_feedback_popup_window import BugsAndFeedbackPopupWindow
from feedback.feedback_plugin_model import FeedbackPluginModel
from feedback.feedback_plugin_presenter import FeedbackPluginPresenter
from eos_util.image import Image


from metrics.time_provider import TimeProvider
from util.feedback_manager import FeedbackManager


class FeedbackPlugin(gtk.EventBox):
    def __init__(self, parent):
        super(FeedbackPlugin, self).__init__()

        self._parent = parent

        self._presenter = FeedbackPluginPresenter(FeedbackPluginModel(FeedbackManager(), TimeProvider()))

        self._pixbuf_normal = Image.from_name('bugs_normal.png')
        self._pixbuf_hover = Image.from_name('bugs_hover.png')
        self._pixbuf_down = Image.from_name('bugs_down.png')

        self._feedback_icon = gtk.Image()

        self._pixbuf_normal.draw(self._feedback_icon.set_from_pixbuf)

        self.set_visible_window(False)
        self.add(self._feedback_icon)

        self.connect("enter-notify-event", lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_hover))
        self.connect("leave-notify-event", lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_normal))
        self.connect('button-press-event', lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_down))
        self.connect('button-release-event',lambda w, e: self.toggle_image(self._feedback_icon, self._pixbuf_normal))

        self.connect('button-press-event', lambda w, e:self._feedback_icon_clicked_callback())

    def toggle_image(self, image, pixbuf):
        pixbuf.draw(image.set_from_pixbuf)

    def _feedback_submitted(self, widget):
        self._presenter.submit_feedback(self._feedback_popup.get_text(), self._feedback_popup.is_bug())
        self._feedback_popup.destroy()
        self._show_feedback_thank_you_message()

    def _show_feedback_thank_you_message(self):
        #spawn wait indicator
        self._feedback_thank_you_dialog = FeedbackResponseDialogView()
        self._feedback_thank_you_dialog.show()
        gobject.timeout_add(3000, self._feedback_thanks_close)

    def _feedback_thanks_close(self):
        self._feedback_thank_you_dialog.destroy()
        return False

    # Show popup
    def _feedback_icon_clicked_callback(self):
        self._feedback_popup = BugsAndFeedbackPopupWindow(self._parent, self._feedback_submitted)
        self._feedback_popup.show()
