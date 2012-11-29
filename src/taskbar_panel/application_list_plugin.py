import gtk
import sys
import time
import Xlib
import array
import threading
from gtk import gdk
from Xlib import Xatom, display, Xutil, X

from taskbar_icon import TaskbarIcon
from threading import Thread
from eos_util.image_util import load_pixbuf

# DO NOT REMOVE!!! PyInstaller cannot know that these are imported
# on its own so we have to manually import them
from Xlib.support import unix_connect
from Xlib.ext import xtest, shape, xinerama, record, composite, randr
# *****************

class ApplicationListPlugin(gtk.HBox):
    def __init__(self, icon_size):
        super(ApplicationListPlugin, self).__init__()

        self._icon_size = icon_size
        pixbuf = load_pixbuf('endless.png')
        self._default_icon = pixbuf.scale_simple(icon_size, icon_size, gdk.INTERP_BILINEAR)
        del pixbuf

        self._taskbar_icons = {}

        self._local_display = display.Display()
        self._screen = self._local_display.screen()

        self._NET_CLIENT_LIST_ATOM_ID       = self._local_display.intern_atom('_NET_CLIENT_LIST')
        self._NET_WM_SKIP_TASKBAR_ATOM_ID   = self._local_display.intern_atom('_NET_WM_STATE_SKIP_TASKBAR')
        self._NET_WM_STATE_ATOM_ID          = self._local_display.intern_atom('_NET_WM_STATE')
        self._NET_WM_ICON_ATOM_ID           = self._local_display.intern_atom('_NET_WM_ICON')
        self._WM_CHANGE_STATE_ATOM_ID       = self._local_display.intern_atom('WM_CHANGE_STATE')
        self._NET_WM_STATE_HIDDEN_ATOM_ID   = self._local_display.intern_atom('_NET_WM_STATE_HIDDEN')
        self._NET_ACTIVE_WINDOW_ATOM_ID     = self._local_display.intern_atom('_NET_ACTIVE_WINDOW')
        self._NET_WM_NAME_ATOM_ID           = self._local_display.intern_atom('_NET_WM_NAME')


        watched_atom_ids = [self._NET_CLIENT_LIST_ATOM_ID,
                            self._NET_ACTIVE_WINDOW_ATOM_ID,
                            self._NET_WM_STATE_ATOM_ID,
                            self._NET_WM_ICON_ATOM_ID,
                            self._NET_WM_NAME_ATOM_ID]



        update_thread = UpdateTasksThread(self._local_display, self._screen,
                                          self._NET_CLIENT_LIST_ATOM_ID, self._NET_ACTIVE_WINDOW_ATOM_ID,
                                          watched_atom_ids, self._draw_tasks)
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

            # Check if the app is requesting not to be in taskbar
            try:
                if self._NET_WM_SKIP_TASKBAR_ATOM_ID in window.get_full_property(self._NET_WM_STATE_ATOM_ID, Xatom.ATOM).value:
                    continue
            except:
                pass

            # Get window name
            window_name = ""
            try:
                window_name = window.get_wm_name()
            except:
                print "Failed to get app name"
                pass

            scaled_pixbuf = self._default_icon
            # Get window's icons
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
                for i, data in enumerate(data_array):
                    data_array[i] = (data & 0xff00ff00) | ((data & 0xff) << 16) | ((data >> 16) & 0xff)

                # Scale the icon
                icon_pixbuf = gdk.pixbuf_new_from_data(data_array.tostring(), gdk.COLORSPACE_RGB, True, 8, width, height, width * 4)
                scaled_pixbuf = icon_pixbuf.scale_simple(self._icon_size, self._icon_size, gdk.INTERP_BILINEAR)
                del icon_pixbuf
            except:
#                print "Error retrieving icon. Using default"
                pass

            # Check if we are the selected task
            is_selected = (selected_window != None) & (len(selected_window) > 0) & (task == selected_window[0])

            if task not in self._taskbar_icons.keys():
                self._application_event_box = TaskbarIcon(task, window_name, scaled_pixbuf, is_selected)
                self._application_event_box.connect("button-press-event", self.toggle_state)
                del scaled_pixbuf

                self._taskbar_icons[task] = self._application_event_box
                self.pack_start(self._application_event_box, False, False, 4)
            else:
                self._taskbar_icons[task].update_task(window_name, scaled_pixbuf, is_selected)

            self.show_all()
        gtk.threads_leave()

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
        except:
            print "Error toggling the task", sys.exc_info()

        try:
            self._local_display.flush()
        except:
            print "Error flushing the display"

class UpdateTasksThread(Thread):
    def __init__(self, display, screen, client_list_atom_id, active_window_atom_id, watched_atom_ids, callback):
        super(UpdateTasksThread, self).__init__()
        self.setDaemon(True)

        self._screen = screen
        self._display = display
        self._client_list_atom_id = client_list_atom_id
        self._active_window_atom_id = active_window_atom_id
        self._watched_atom_ids = watched_atom_ids

        self._draw_tasks_callback = callback

    def run(self):
        # Attach  to root screen property changes
        self._screen.root.change_attributes(event_mask=(
            X.PropertyChangeMask | X.FocusChangeMask | X.StructureNotifyMask))

        # Force the first update on start
        needs_update = True

        # Main loop
        while True :
            # Are there pending events waiting for us
            while self._display.pending_events():
                event = self._display.next_event()

                # If we haven't set the update flag yet, check if it matches our watched list
                if not needs_update:
                    try:
                        if event.type == X.PropertyNotify and hasattr(event, 'atom') and event.atom in self._watched_atom_ids:
                            # Set needs update flag since it is something we care about
                            needs_update = True
                    except:
                        print >> sys.stderr, "Could not retrieve change atom IDs. Continuing"

            # Taskbar needs updating
            if needs_update:
                try:
                    tasks = self._screen.root.get_full_property(self._client_list_atom_id, Xatom.WINDOW).value
                    selected_window = self._screen.root.get_full_property(self._active_window_atom_id, Xatom.WINDOW).value
                    self._draw_tasks_callback(tasks, selected_window)
                except:
                    print >> sys.stderr, "Could not retrieve tasks. Continuing"

            needs_update = False

            # Sleep so that we don't waste CPU cycles
            time.sleep(0.25)





