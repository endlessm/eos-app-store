from icon_plugin import IconPlugin
from ui.abstract_notifier import AbstractNotifier
from panel_constants import PanelConstants

class NetworkPluginView(AbstractNotifier, IconPlugin):
    ICON_NAMES = ['wifi_off.png', 'wifi_low.png', 'wifi_med.png', 'wifi_full.png'] 

    HORIZONTAL_MARGIN = 4
     
    def __init__(self, parent, icon_size):
        super(NetworkPluginView, self).__init__(icon_size, self.ICON_NAMES, None)
       
        self.set_margin(self.HORIZONTAL_MARGIN)

        self._window = None

        self._parent = parent
        self._parent.connect("expose-event", self._draw)

    def display_network_state(self, state):
        # assuming that state agregates connection status and signal strength,
        # display them both in some way.
        self.display_network_strength(state)

    def display_network_strength(self, strength):
        self._strength = strength 
        
        self._parent.set_visible_window(False)
        self._parent.set_size_request(PanelConstants.get_icon_size() + 2 * self.HORIZONTAL_MARGIN, PanelConstants.get_icon_size())
        
        # TODO show network icon if no wifi but only lan connected
#         if self._level == None:
#             self._parent.hide()
#         else:
        self._parent.show()
        self._set_icon(self._strength)
        
        self.queue_draw()
        self._parent.queue_draw()
    
    def _set_icon(self, strength):
        if strength > 65:
            self._set_index(3)
        elif strength > 32:
            self._set_index(2)
        elif strength > 0:
            self._set_index(1)
        else:
            self._set_index(0)
            