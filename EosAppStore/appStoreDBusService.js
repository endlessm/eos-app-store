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
