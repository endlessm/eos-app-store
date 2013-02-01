from threading import Thread
import dbus
import dbus.service
import dbus.mainloop.glib

import gobject

class EndlessDesktopService(dbus.service.Object):
    def __init__(self, desktop_presenter):
        self._desktop_presenter = desktop_presenter

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus_name = dbus.service.BusName("com.endless.desktop", dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, "/com/endless/desktop")

    def start_service(self):
        self._running_thread = Thread(target=self._process)
        self._running_thread.setDaemon(True)
        self._running_thread.start()

    def _process(self):
        log.info("Desktop service running...")
        gobject.MainLoop().run()
        log.info("Desktop service stopped.")

    @dbus.service.method("com.endless.Desktop", in_signature='s', out_signature='')
    def choose_background(self, filename):
        self._desktop_presenter.change_background(filename)

    @dbus.service.method("com.endless.Desktop", in_signature='', out_signature='')
    def revert_background(self):
        self._desktop_presenter.revert_background()
