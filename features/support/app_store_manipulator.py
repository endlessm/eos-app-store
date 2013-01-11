import sys
from ldtp import *
import time

class AppStoreManipulator():
   def click_through(self):
      generatemouseevent(800,700)
      time.sleep(0.3)
      generatemouseevent(190,660)
      time.sleep(0.3)
      generatemouseevent(100,100)
      time.sleep(0.1)
