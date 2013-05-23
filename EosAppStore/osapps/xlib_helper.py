from Xlib import Xatom, display, X, protocol, Xutil

from EosAppStore.eos_log import log
from EosAppStore.osapps.display_provider import DisplayProvider

class XlibHelper():
    # Xlib atom names
    _ATOMS = dict(
            CLIENT_LIST         = '_NET_CLIENT_LIST',
            SKIP_TASKBAR        = '_NET_WM_STATE_SKIP_TASKBAR',
            WINDOW_STATE        = '_NET_WM_STATE',
            ICON                = '_NET_WM_ICON',
            WINDOW_CHANGE_STATE = 'WM_CHANGE_STATE',
            WINDOW_STATE_HIDDEN = '_NET_WM_STATE_HIDDEN',
            ACTIVE_WINDOW       = '_NET_ACTIVE_WINDOW',
            PROCESS_ID          = '_NET_WM_PID',
            WINDOW_NAME         = '_NET_WM_NAME',
            UTF8                = 'UTF8_STRING',
            )
    Atom = type('Enum', (), _ATOMS)

    def __init__(self, display_provider=DisplayProvider(), logger = log):
        self._display = display_provider.display()
        self._screen = self._display.screen()
        self._logger = log
        self._window_name_atom_id = self.get_atom_id(XlibHelper.Atom.WINDOW_NAME)
        self._utf8_atom_id = self.get_atom_id(XlibHelper.Atom.UTF8)
        self._active_window_atom_id = self.get_atom_id(XlibHelper.Atom.ACTIVE_WINDOW)

    def get_atom_id(self, atom_id):
        return self._display.intern_atom(atom_id) 

    def get_window_name(self, window):
        window_name = ""
        try:
            try:
                window_name = window.get_full_property(self._window_name_atom_id, self._utf8_atom_id).value
            except (NameError, AttributeError) as e:
                pass
            except Exception as e:
                self._logger.error("Could not retrieve window name by default means. Continuing.", e)

            if window_name:
                window_name = unicode(window_name, 'utf-8')
            else:
                window_name = unicode(window.get_wm_name())
        except Exception as e:
            self._logger.error("Failed to get window name. Continuing", e)

        return window_name

    def get_selected_window_class_name(self, root_window):
        selected_window_name = None
        try:
            selected_window_id = root_window.get_full_property(self._active_window_atom_id, Xatom.WINDOW).value[0]
            window = self._display.create_resource_object('window', selected_window_id)

            selected_window_name = window.get_wm_class()[1]
        except Exception as e:
            self._logger.error("Failed to get window class. Continuing", e)

        return selected_window_name

    def _bring_window_to_front(self, window):
        try:
            clientmessage = protocol.event.ClientMessage(
                client_type=self.get_atom_id(XlibHelper.Atom.ACTIVE_WINDOW),
                window=window,
                data=(32, (2, X.CurrentTime, 0, 0, 0))
            )
            self._screen.root.send_event(clientmessage, (X.SubstructureRedirectMask | X.SubstructureNotifyMask))
        except Exception as e:
            log.error("Error raising the window", e)

    def _get_all_tasks(self):
        return self._screen.root.get_full_property(self.get_atom_id(XlibHelper.Atom.CLIENT_LIST), Xatom.WINDOW).value

    def _find_app_window(self, app_key):
        for task in self._get_all_tasks():
            window = self._display.create_resource_object('window', task)
            if self.get_application_key(window) == app_key:
                return window
        return None

    def bring_app_to_front(self, app_key):
        window = self._find_app_window(app_key)
        if window:
            self._bring_window_to_front(window)
            return True
        return False

    # Note: the class name may have mixed capitalization.
    # If comparing with the name of the executable binary,
    # it is recommended that the caller convert both to all lower case.
    # Some applications might not report a WM_CLASS property,
    # in which case the return value is a blank string.

    def get_class_name(self, window):
        class_name = ""
        try:
            class_name = window.get_wm_class()[1]
        except Exception as e:
            self._logger.error("Failed to get class name. Continuing", e)

        return class_name

    # Gets a key (all lower-case) for the application that can be used to retrieve details
    # about the application's desktop file (such as its icon name) from a dictionary
    def get_application_key(self, window):
        key = self.get_class_name(window)
        if not key:
            key = self.get_window_name(window)
        return key.lower()

