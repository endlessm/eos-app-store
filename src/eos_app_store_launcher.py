#!/usr/bin/env python
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from app_store.eos_app_store import EosAppStore
import sys

if __name__ == "__main__":
   app = EosAppStore()

   GObject.threads_init()
   Gdk.threads_init()
   exit_status = app.run(sys.argv)
   sys.exit(exit_status)

