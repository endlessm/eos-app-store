// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const Lang = imports.lang;

const APP_STORE_PATH = '/com/endlessm/AppStore';
const APP_STORE_IFACE = 'com.endlessm.AppStore';

const AppStoreDBusIface = '<node><interface name="com.endlessm.AppStore">' +
  '<method name="show">' +
    '<arg type="u" direction="in" name="timestamp"/>' +
    '<arg type="b" direction="in" name="reset"/>' +
  '</method>' +
  '<method name="hide">' +
    '<arg type="u" direction="in" name="timestamp"/>' +
  '</method>' +
  '<method name="showPage">' +
    '<arg type="u" direction="in" name="timestamp"/>' +
    '<arg type="s" direction="in" name="page"/>' +
  '</method>' +
  '<method name="ListInstalled">' +
    '<arg type="a(s)" direction="out" name="applications"/>' +
  '</method>' +
  '<method name="ListUpdatable">' +
    '<arg type="a(s)" direction="out" name="applications"/>' +
  '</method>' +
  '<method name="ListUninstallable">' +
    '<arg type="a(s)" direction="out" name="applications"/>' +
  '</method>' +
  '<method name="ListAvailable">' +
    '<arg type="a(s)" direction="out" name="applications"/>' +
  '</method>' +
  '<method name="Refresh">' +
    '<arg type="b" direction="out" name="success"/>' +
  '</method>' +
  '<method name="Install">' +
    '<arg type="s" direction="in" name="app_id"/>' +
    '<arg type="b" direction="out" name="success"/>' +
  '</method>' +
  '<method name="Uninstall">' +
    '<arg type="s" direction="in" name="app_id"/>' +
    '<arg type="b" direction="out" name="success"/>' +
  '</method>' +
  '<property name="Visible" type="b" access="read"/>' +
'</interface></node>';

const AppStoreDBusService = new Lang.Class({
    Name: 'AppStoreDBusService',

    _init: function(app) {
        this._app = app;
        this._dbusImpl = Gio.DBusExportedObject.wrapJSObject(AppStoreDBusIface, this);
        this._dbusImpl.export(Gio.DBus.session, APP_STORE_PATH);
    },

    show: function(timestamp, reset) {
        this._app.show(reset, timestamp);
    },

    hide: function(timestamp) {
        this._app.hide();
    },

    showPage: function(timestamp, page) {
        this._app.showPage(timestamp, page);
    },

    ListInstalled: function() {
        print("Stub!");
        return [];
    },

    ListUpdatable: function() {
        print("Stub!");
        return [];
    },

    ListUninstallable: function() {
        print("Stub!");
        return [];
    },

    ListAvailable: function() {
        print("Stub!");
        return [];
    },

    RefreshAsync: function(params, invocation) {
        log("Refreshing apps");
        this._app.appList.refresh(Lang.bind(this, function(error) {
            let success = (error == null);
            invocation.return_value(GLib.Variant.new('(b)', [success]));
        }));
    },

    Install: function(appId) {
        print("Stub! -", appId);
        return true;
    },

    Uninstall: function(appId) {
        print("Stub! -", appId);
        return true;
    },

    visibilityChanged: function(is_visible) {
        this._visible = is_visible;

        let propChangedVariant = new GLib.Variant('(sa{sv}as)',
            [APP_STORE_IFACE, { 'Visible': new GLib.Variant('b', this._visible) }, []]);

        Gio.DBus.session.emit_signal(null, APP_STORE_PATH,
                                     'org.freedesktop.DBus.Properties',
                                     'PropertiesChanged',
                                     propChangedVariant);
    }
});
