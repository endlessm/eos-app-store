const Gio = imports.gi.Gio;
const Lang = imports.lang;

const AppManagerIface = '\
<node> \
  <interface name="com.endlessm.AppManager"> \
    <method name="GetUserCapabilities">
      <arg type="a{sv}" direction="out" /> \
    </method>
    <method name="Refresh"> \
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
        this._canRefresh = false;
        this._canInstall = false;
        this._canUninstall = false;

        this._proxy = new AppManagerProxy(Gio.DBus.system,
                                          APP_MANAGER_NAME,
                                          APP_MANAGER_PATH);
    },

    getUserCapabilities: function(callback) {
        this._proxy.GetUserCapabilitiesRemote(Lang.bind(this,
                                                        this._getUserCapabilitiesFinished,
                                                        callback));
    },

    _getUserCapabilitiesFinished: function(result, error, callback) {
        if (error) {
            log('Unable to retrieve user capabilities: ' + error);
            return;
        }

        let caps = result[0];

        this._canRefresh = caps['CanRefresh'];
        this._canInstall = caps['CanInstall'];
        this._canUninstall = caps['CanUninstall'];

        callback();
    },

    get canRefresh() {
        return this._canRefresh;
    },

    get canInstall() {
        return this._canInstall;
    },

    get canUinstall() {
        return this._canUninstall;
    },

    refresh: function() {
        this._proxy.RefreshRemote();
    }
});
