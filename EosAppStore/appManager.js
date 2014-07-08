const Gio = imports.gi.Gio;
const Lang = imports.lang;

const AppManagerIface = '\
<node> \
  <interface name="com.endlessm.AppManager"> \
    <method name="Refresh"> \
      <arg type="a{sv}" direction="in" /> \
      <arg type="b" direction="out" /> \
    </method> \
    </interface> \
</node>';

const APP_MANAGER_NAME = 'com.endlessm.AppManager';
const APP_MANAGER_PATH = '/com/endlessm/AppManager';
const APP_MANAGER_IFACE = 'com.endlessm.AppManager';

const AppManagerProxy = Gio.DBusProxy.makeProxyWrapper(AppManagerIface);

const AppManager = new Lang.Class({
    Name: 'AppManager',

    _init: function() {
        this.proxy = new AppManagerProxy(Gio.DBus.system,
            APP_MANAGER_NAME, APP_MANAGER_PATH);
    }
});
