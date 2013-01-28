from eos_log import log

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
            WINDOW_NAME         = '_NET_WM_NAME',
            UTF8                = 'UTF8_STRING',
            )
    Atom = type('Enum', (), _ATOMS)
    
    def __init__(self, display, logger = log):
        self._display = display
        self._logger = log
        self._window_name_atom_id = self.get_atom_id(XlibHelper.Atom.WINDOW_NAME)
        self._utf8_atom_id = self.get_atom_id(XlibHelper.Atom.UTF8)
    
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