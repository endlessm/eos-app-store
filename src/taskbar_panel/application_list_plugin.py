import gtk
import Xlib
import array
from gtk import gdk
from Xlib import Xatom, display, Xutil, X

from eos_log import log
from taskbar_icon import TaskbarIcon
from eos_util.image_util import load_pixbuf
from update_task_thread import UpdateTasksThread
from xlib_helper import XlibHelper
from predefined_icons_provider import PredefinedIconsProvider

# DO NOT REMOVE!!! PyInstaller does not know that these are imported
# on its own so we have to manually import them
from Xlib.support import unix_connect
from Xlib.ext import xtest, shape, xinerama, record, composite, randr
# *****************

class ApplicationListPlugin(gtk.HBox):
    def __init__(self, icon_size, local_display = display.Display(), pixbuf_loader = load_pixbuf, predefined_icons_provider = PredefinedIconsProvider()):
        super(ApplicationListPlugin, self).__init__()

        self._icon_size = icon_size
        pixbuf = pixbuf_loader('endless.png')
        self._default_icon = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)

        self._taskbar_icons = {}

        self._local_display = local_display
        self._screen = self._local_display.screen()
        self._predefined_icons_provider = predefined_icons_provider 

        self._xlib_helper = XlibHelper(local_display)

        self._NET_CLIENT_LIST_ATOM_ID       = self._xlib_helper.get_atom_id(XlibHelper.Atom.CLIENT_LIST)
        self._NET_WM_SKIP_TASKBAR_ATOM_ID   = self._xlib_helper.get_atom_id(XlibHelper.Atom.SKIP_TASKBAR)
        self._NET_WM_STATE_ATOM_ID          = self._xlib_helper.get_atom_id(XlibHelper.Atom.WINDOW_STATE)
        self._NET_WM_ICON_ATOM_ID           = self._xlib_helper.get_atom_id(XlibHelper.Atom.ICON)
        self._WM_CHANGE_STATE_ATOM_ID       = self._xlib_helper.get_atom_id(XlibHelper.Atom.WINDOW_CHANGE_STATE)
        self._NET_WM_STATE_HIDDEN_ATOM_ID   = self._xlib_helper.get_atom_id(XlibHelper.Atom.WINDOW_STATE_HIDDEN)
        self._NET_ACTIVE_WINDOW_ATOM_ID     = self._xlib_helper.get_atom_id(XlibHelper.Atom.ACTIVE_WINDOW)
        self._NET_WM_NAME_ATOM_ID           = self._xlib_helper.get_atom_id(XlibHelper.Atom.WINDOW_NAME)
        self._UTF8_ATOM_ID           	    = self._xlib_helper.get_atom_id(XlibHelper.Atom.UTF8)

        watched_atom_ids = [self._NET_CLIENT_LIST_ATOM_ID,
                            self._NET_ACTIVE_WINDOW_ATOM_ID,
                            self._NET_WM_STATE_ATOM_ID,
                            self._NET_WM_ICON_ATOM_ID,
                            self._NET_WM_NAME_ATOM_ID]

        update_thread = UpdateTasksThread(self._local_display, 
                                          self._screen,
                                          self._NET_CLIENT_LIST_ATOM_ID, 
                                          self._NET_ACTIVE_WINDOW_ATOM_ID,
                                          watched_atom_ids, 
                                          self._draw_tasks)
        update_thread.start()

        self.show_all()

    def _draw_tasks(self, tasks, selected_window):
        gtk.threads_enter()

        for taskbar_icon in self._taskbar_icons.keys():
            if taskbar_icon not in tasks:
                self.remove(self._taskbar_icons[taskbar_icon])
                self._taskbar_icons[taskbar_icon].destroy()
                del self._taskbar_icons[taskbar_icon]

        for task in tasks:
            # Get window object from ID
            window = self._local_display.create_resource_object('window', task)

            if not self._should_app_be_in_taskbar(window):
                continue

            window_name = self._xlib_helper.get_window_name(window)
            scaled_icon = self._get_window_icon(window)

            # Check if we are the selected task
            is_selected = (selected_window != None) & (len(selected_window) > 0) & (task == selected_window[0])

            if task not in self._taskbar_icons.keys():
                self._application_event_box = TaskbarIcon(task, window_name, scaled_icon, is_selected)
                self._application_event_box.connect("button-press-event", self.toggle_state)

                self._taskbar_icons[task] = self._application_event_box
                self.pack_start(self._application_event_box, False, False, 4)
            else:
                self._taskbar_icons[task].update_task(window_name, scaled_icon, is_selected)

            self.show_all()
        gtk.threads_leave()

    def _should_app_be_in_taskbar(self, window):
        retval = True
        # Check if the app is requesting not to be in taskbar
        try:
            if self._NET_WM_SKIP_TASKBAR_ATOM_ID in window.get_full_property(self._NET_WM_STATE_ATOM_ID, Xatom.ATOM).value:
                retval = False
        except:
            pass
        
        # Do not display Firefox in the taskbar
        if self._xlib_helper.get_application_key(window) == 'firefox':
            retval = False
            
        return retval
            
    def _get_window_icon(self, window):
        # Get the window's icon if it was predefined
        icon = self._get_predefined_icon(window)

        # Otherwise grab it from X11
        if not icon:
            icon = self._get_x11_icon(window)

        # Default icon if all else fails
        if not icon:
            icon = self._default_icon

        return icon

    def _get_predefined_icon(self, window):
        try:
            application_key = self._xlib_helper.get_application_key(window)
            return self._predefined_icons_provider.get_icon_for(application_key)
        except:
            return None

    def _get_x11_icon(self, window):
        try:
            icon = window.get_full_property(self._NET_WM_ICON_ATOM_ID, Xatom.CARDINAL)
            if icon is None or icon.format != 32:
                raise Exception("Icon is not in a good format. Using default")

            # Extract icon data. We should also check other icons
            width = icon.value[0]
            height = icon.value[1]
            data = icon.value[2:width * height + 2]
            data_array = array.array('I', data)

            # Convert ARGB to ABRG
            for index, data in enumerate(data_array):
                data_array[index] = (data & 0xff00ff00) | ((data & 0xff) << 16) | ((data >> 16) & 0xff)

            # Scale the icon
            icon_pixbuf = gdk.pixbuf_new_from_data(data_array.tostring(), gdk.COLORSPACE_RGB, True, 8, width, height, width * 4)
            scaled_pixbuf = icon_pixbuf.scale_simple(self._icon_size, self._icon_size, gdk.INTERP_BILINEAR)
            del icon_pixbuf

            return scaled_pixbuf
        except:
            return None

    def toggle_state(self, widget, event):
        try:
            window = self._local_display.create_resource_object('window', widget.task())
            if (Xutil.IconicState != window.get_wm_state()['state']) & widget.is_selected():
                clientmessage = Xlib.protocol.event.ClientMessage(
                    client_type=self._WM_CHANGE_STATE_ATOM_ID,
                    window=window,
                    data=(32, ([Xutil.IconicState, 0, 0, 0, 0]))
                )
                self._screen.root.send_event(clientmessage, (X.SubstructureRedirectMask | X.SubstructureNotifyMask))
            else:
                clientmessage = Xlib.protocol.event.ClientMessage(
                    client_type=self._NET_ACTIVE_WINDOW_ATOM_ID,
                    window=window,
                    data=(32, (2, X.CurrentTime, 0, 0, 0))
                )
                self._screen.root.send_event(clientmessage, (X.SubstructureRedirectMask | X.SubstructureNotifyMask))
        except Exception as e:
            log.error("Error toggling the task", e)

        try:
            self._local_display.flush()
        except Exception as e:
            log.error("Error flushing the display", e)
