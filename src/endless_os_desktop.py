#!/usr/bin/env python
import gtk
import gobject

from desktop_builder import build_desktop

if __name__ == "__main__":

   build_desktop()

   gobject.threads_init()
   gtk.threads_init()
   gtk.main()
