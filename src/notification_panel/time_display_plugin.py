import gtk
from gtk import gdk

import datetime
import gobject

class TimeDisplayPlugin(gtk.EventBox):
    def __init__(self, icon_size):
        super(TimeDisplayPlugin, self).__init__()
        
        self._time_label = gtk.Label()
        self._update_time()
        
        new_style = self._time_label.get_style().copy()
        new_style.fg[gtk.STATE_NORMAL] = self._time_label.get_colormap().alloc('#f0f0f0')
        self._time_label.set_style(new_style)
        
        self.set_visible_window(False)
        self.add(self._time_label)
        
        gobject.timeout_add(10000, self._update_time)
    
    def _update_time(self):
        try:
            date = datetime.datetime.now().strftime('%b %d | %H:%M %p').upper()
            formatted_date = '<span size="medium" weight="bold">' + date + '</span>'
            self._time_label.set_markup(formatted_date)
        except:
            pass
        
        return True
        
    @staticmethod
    def get_launch_command():
        return 'sudo gnome-control-center --class=eos-network-manager datetime'
