#!/usr/bin/env python
import gtk
import gobject
from desktop.endless_desktop_view import EndlessDesktopView

if __name__ == "__main__":
   view = EndlessDesktopView()

   gobject.threads_init()
   gtk.threads_init()
   gtk.main()
