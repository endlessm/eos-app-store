import gettext
import gtk

from icon_plugin import IconPlugin
from ui.abstract_notifier import AbstractNotifier
from util.transparent_window import TransparentWindow
from eos_util import screen_util
from panel_constants import PanelConstants

gettext.install('endless_desktop', '/usr/share/locale', unicode = True, names=['ngettext'])

class AllSettingsView(AbstractNotifier):
    X_OFFSET = 13
    WINDOW_WIDTH = 330
    WINDOW_HEIGHT = 160
    WINDOW_BORDER = 10

    DESKTOP_BACKGROUND = "desktop_background"
    UPDATE_SOFTWARE = "update_software"
    SETTINGS = "settings"
    LOGOUT = "logout"
    RESTART = "restart"
    SHUTDOWN = "shutdown"
    
    UPDATE_BUTTON_TEXT = _('Update')
    UPDATE_IN_PROGRESS_BUTTON_TEXT = _('Updating...')

    RESTART_MESSAGE = 1
    SHUTDOWN_MESSAGE = 2
    LOGOUT_MESSAGE = 4

    _messages = {
                    RESTART_MESSAGE:  _("Restart?"),
                    SHUTDOWN_MESSAGE: _("Shutdown?"),
                    LOGOUT_MESSAGE:   _("Log Out?"),
                }

    def __init__(self, parent):
        self._parent = parent
        self._button_desktop = gtk.Button(_('Background'))
        self._label_version = gtk.Label()
        self._button_update = gtk.Button(self.UPDATE_BUTTON_TEXT)
        self._button_settings = gtk.Button(_('Settings'))
        self._button_logout = gtk.Button(_('Log Out'))
        self._button_restart = gtk.Button(_('Restart'))
        self._button_shutdown = gtk.Button(_('Shut Down'))

        self._button_desktop.connect('button-press-event',
                lambda w, e: self._notify(self.DESKTOP_BACKGROUND))
        self._button_update.connect('button-release-event',
                lambda w, e: self._notify(self.UPDATE_SOFTWARE))
        self._button_settings.connect('button-release-event',
                lambda w, e: self._notify(self.SETTINGS))
        self._button_logout.connect('button-release-event',
                lambda w, e: self._notify(self.LOGOUT))
        self._button_restart.connect('button-release-event',
                lambda w, e: self._notify(self.RESTART))
        self._button_shutdown.connect('button-release-event',
                lambda w, e: self._notify(self.SHUTDOWN))

        self._table = gtk.Table(5, 3, True)
        self._table.set_border_width(10)
        self._table.set_focus_chain([])
        self._table.attach(self._label_version, 0, 3, 0, 1)
        self._table.attach(self._button_settings, 0, 3, 1, 2)
        self._table.attach(self._button_desktop, 0, 3, 2, 3)
        self._table.attach(self._button_update, 0, 3, 3, 4)
        self._table.attach(self._button_logout, 0, 1, 4, 5)
        self._table.attach(self._button_restart, 1, 2, 4, 5)
        self._table.attach(self._button_shutdown, 2, 3, 4, 5)

        self._parent.set_visible_window(False)
    
        self._window = TransparentWindow(self._parent.get_toplevel())

        x = screen_util.get_width() - self.WINDOW_WIDTH - self.X_OFFSET

        # Get the x location of the center of the widget (icon), relative to the settings window
        self._window.move(x, PanelConstants.DEFAULT_POPUP_VERTICAL_MARGIN)
        
        self._window.set_size_request(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self._window.set_border_width(self.WINDOW_BORDER)

        # Set up the window so that it can be exposed
        # with a transparent background and triangle decoration
        self._window.connect('expose-event', self._expose)

        self._window.connect('focus-out-event', lambda w, e: self.hide_window())

        # Place the widget in an event box within the window
        # (which has a different background than the transparent window)
        self._container = gtk.EventBox()
        self._container.add(self._table)
        self._window.add(self._container)
        self._is_active = False

    def set_current_version(self, version_text):
        self._label_version.set_text(version_text)

    # To do: make the triangle position configurable
    def _expose(self, widget, event):
        cr = widget.window.cairo_create()

        # Decorate the border with a triangle pointing up
        # Use the same color as the default event box background
        # To do: eliminate need for these "magic" numbers
        cr.set_source_rgba(0xf2/255.0, 0xf1/255.0, 0xf0/255.0, 1.0)
        self._pointer = 300
        cr.move_to(self._pointer, 0)
        cr.line_to(self._pointer + 10, 10)
        cr.line_to(self._pointer - 10, 10)
        cr.fill()

    def confirm(self, message_id):
        dialog = gtk.Dialog("Confirmation", self._parent._parent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        dialog.set_decorated(False)
        dialog.set_border_width(10)
        dialog.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO)
        dialog.set_position(gtk.WIN_POS_CENTER)
        message = self._get_confirm_message(message_id)
        label = gtk.Label(message)
        label.show()
        dialog.vbox.pack_start(label)
        answer = dialog.run()
        dialog.destroy()

        return (answer == gtk.RESPONSE_YES)

    def _get_confirm_message(self, message_id):
        if message_id in self._messages:
            return self._messages[message_id]

    def display(self):
        self._window.show_all()

    def hide_window(self):
        self._window.destroy()
        
    def enable_update_button(self):
        self._button_update.set_sensitive(True)
        self._button_update.set_label(self.UPDATE_BUTTON_TEXT)

    def disable_update_button(self):
        self._button_update.set_sensitive(False)
        self._button_update.set_label(self.UPDATE_IN_PROGRESS_BUTTON_TEXT)
        
    def inform_user_of_update(self): 
        info_message = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, 
            gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE,
            _("Downloading updates to the EndlessOS. We will notify you once the updates are ready to install.")
             )
        info_message.connect("response", lambda w, id: info_message.destroy()) 
        info_message.show() 
        
        
