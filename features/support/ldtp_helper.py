from ldtp import *
import glib
import os
import sys
import dbus
import dbus.mainloop.glib
import json
import time

class LdtpHelper():
    DEFAULT_SLEEP_AMOUNT = 0.2
    
    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        service = bus.get_object('com.endlessm.uat.Desktop', "/com/endlessm/uat/Desktop")
        self._method = service.get_dbus_method('get_stuff', 'com.endlessm.uat.Desktop')
        
    def click_on(self, widget_id, sleep_amount=DEFAULT_SLEEP_AMOUNT):
        x, y =  self._get_widget(widget_id)["coord"]
        generatemouseevent(x, y)
        
        time.sleep(sleep_amount)

    def _get_widget(self, widget_id):
        try:
            data = json.loads(self._method())
        except Exception as e:
            print >> sys.stderr, "Error!", e
            sys.exit(1)
        
        return data[widget_id]
