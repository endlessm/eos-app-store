import gtk
from gtk import gdk

from Xlib import Xatom, display, Xutil, X #X, display, error, Xatom, Xutil

from util.image_util import load_pixbuf
import Xlib
from taskbar_icon import TaskbarIcon

class ApplicationListPlugin(gtk.HBox):
    def __init__(self, icon_size):
        super(ApplicationListPlugin, self).__init__()
        pixbuf = load_pixbuf('bluetooth.png')
        scaled_pixbuf = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        
        del pixbuf
        
        self._local_display = display.Display()
        self._screen = self._local_display.screen()

        self._NET_CLIENT_LIST_ATOM_ID       = self._local_display.intern_atom('_NET_CLIENT_LIST')
        self._NET_WM_SKIP_TASKBAR_ATOM_ID   = self._local_display.intern_atom('_NET_WM_STATE_SKIP_TASKBAR')
        self._NET_WM_STATE_ATOM_ID          = self._local_display.intern_atom('_NET_WM_STATE')
        self._NET_WM_ICON_ATOM_ID           = self._local_display.intern_atom('_NET_WM_ICON')
        self._WM_CHANGE_STATE_ATOM_ID       = self._local_display.intern_atom('WM_CHANGE_STATE')
        self._NET_WM_STATE_HIDDEN_ATOM_ID   = self._local_display.intern_atom('_NET_WM_STATE_HIDDEN')
        self._NET_ACTIVE_WINDOW_ATOM_ID     = self._local_display.intern_atom('_NET_ACTIVE_WINDOW')
        

        tasks = self._screen.root.get_full_property(self._NET_CLIENT_LIST_ATOM_ID, Xatom.WINDOW).value
        for task in tasks:
            resource = self._local_display.create_resource_object('window', task)
            try:
                if self._NET_WM_SKIP_TASKBAR_ATOM_ID in resource.get_full_property(self._NET_WM_STATE_ATOM_ID, Xatom.ATOM).value:
                    continue
            except:
                pass
            
            window_name = resource.get_wm_name()
            print "-",window_name
            
            icon = resource.get_full_property(self._NET_WM_ICON_ATOM_ID, 0).value
#            print "width = ", icon[0], " height = ", icon[1] #, " data = ", icon[2:icon[0]*icon[1]+2].tostring()
            
            self._application_event_box = TaskbarIcon(task, window_name, scaled_pixbuf)
            self._application_event_box.connect("button-release-event", self.toggle_state)
            self.pack_start(self._application_event_box, False, False, 4)
            
        del scaled_pixbuf
        
        self.show_all()
        
    def toggle_state(self, widget, event):
        window = self._local_display.create_resource_object('window', widget.task())
#        for func in dir(window):
#            print func 
            
        if  Xutil.IconicState != window.get_wm_state()['state']:
            print "minimizing"
            clientmessage = Xlib.protocol.event.ClientMessage(
                client_type=self._WM_CHANGE_STATE_ATOM_ID,
                window=window,
                data=(32, ([Xutil.IconicState, 0, 0, 0, 0]))
            )
            self._screen.root.send_event(clientmessage, (X.SubstructureRedirectMask|X.SubstructureNotifyMask))
        else:
            print "maximizing"
            clientmessage = Xlib.protocol.event.ClientMessage(
                client_type=self._NET_ACTIVE_WINDOW_ATOM_ID, 
                window=window,
                data=(32, (2, X.CurrentTime, 0, 0, 0))
            )
            self._screen.root.send_event(clientmessage, (X.SubstructureRedirectMask|X.SubstructureNotifyMask))

        self._local_display.flush()
