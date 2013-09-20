const Gio = imports.gi.Gio;
const Lang = imports.lang;

const AppStoreIface = <interface name="org.gnome.Shell.AppStore">
<method name="AddApplication">
    <arg type="s" direction="in" name="id" />
</method>
<method name="RemoveApplication">
    <arg type="s" direction="in" name="id" />
</method>
<method name="ListApplications">
    <arg type="as" direction="out" name="applications" />
</method>
<method name="AddFolder">
    <arg type="s" direction="in" name="id" />
</method>
<method name="RemoveFolder">
    <arg type="s" direction="in" name="id" />
</method>
<signal name="ApplicationsChanged">
    <arg type="as" name="applications" />
</signal>
</interface>;

const SHELL_APP_STORE_NAME = 'org.gnome.Shell';
const SHELL_APP_STORE_PATH = '/org/gnome/Shell';
const SHELL_APP_STORE_IFACE = 'org.gnome.Shell.AppStore';

const ShellAppStoreProxy = Gio.DBusProxy.makeProxyWrapper(AppStoreIface);

const ShellAppStore = new Lang.Class({
    Name: 'ShellAppStore',

    _init: function() {
        this.proxy = new ShellAppStoreProxy(Gio.DBus.session,
            SHELL_APP_STORE_NAME, SHELL_APP_STORE_PATH,
            Lang.bind(this, this._onProxyConstructed));
    },

    _onProxyConstructed: function() {
        // do nothing
    }
});
