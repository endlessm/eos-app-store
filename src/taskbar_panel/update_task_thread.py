import time
from Xlib import X, Xatom
from threading import Thread
from eos_log import log

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
                    except Exception as e:
                        log.error("Could not retrieve change atom IDs. Continuing", e)

            # Taskbar needs updating
            if needs_update:
                try:
                    tasks = self._screen.root.get_full_property(self._client_list_atom_id, Xatom.WINDOW).value
                    selected_window = self._screen.root.get_full_property(self._active_window_atom_id, Xatom.WINDOW).value
                    self._draw_tasks_callback(tasks, selected_window)
                except Exception as e:
                        log.error("Could not retrieve tasks. Continuing", e)

            needs_update = False

            # Sleep so that we don't waste CPU cycles
            time.sleep(0.25)