#!/usr/bin/env python
import gtk
import gobject

from desktop_builder import build_desktop
from startup.initial_tasks import InitialTasks
from startup.startup_tasks import StartupTasks

if __name__ == "__main__":
   InitialTasks().perform_tasks()
   StartupTasks().perform_tasks()

   build_desktop()

   gobject.threads_init()
   gtk.threads_init()
   gtk.main()
