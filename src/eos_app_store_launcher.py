#!/usr/bin/env python
import gtk
import gobject
from app_store.eos_app_store import EosAppStore

if __name__ == "__main__":
   EosAppStore()

   gobject.threads_init()
   gtk.threads_init()
   gtk.main()
