from lettuce import *
import glib
import os
import sys
import signal
import os.path
import time

@before.all
def setUp():
   argv = [
         '/usr/bin/python', 
         './src/endless_os_desktop.py', 
         'uat', 
         ]
   tpid, tstdin, tstout, tsterr = glib.spawn_async(argv)
   world.tpid = tpid

   time.sleep(1)

   if not os.path.exists("/proc/" + str(world.tpid)):
      print >> sys.stderr, "Error! Could not start the desktop!"
      sys.exit(1)

@after.all
def tearDown(total):
   os.kill(world.tpid, signal.SIGTERM)
