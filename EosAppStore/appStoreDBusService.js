// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const Lang = imports.lang;

const EosAppStorePrivate = imports.gi.EosAppStorePrivate;

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
    '<arg type="as" direction="out" name="applications"/>' +
  '</method>' +
  '<method name="ListUpdatable">' +
    '<arg type="as" direction="out" name="applications"/>' +
  '</method>' +
  '<method name="ListUninstallable">' +
    '<arg type="as" direction="out" name="applications"/>' +
  '</method>' +
  '<method name="ListAvailable">' +
    '<arg type="as" direction="out" name="applications"/>' +
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

    ListInstalledAsync: function(params, invocation) {
        log("Listing installed apps");
        this._app.appList.refresh(Lang.bind(this, function(error) {
            let success = (error == null);
            log("Refresh finished. Loading installed apps");

            /* TODO: Handle refresh errors better */
            if (!success)
                invocation.return_value(GLib.Variant.new('(as)', [[]]));

            let appInfos = this._app.appList.loadCategory(EosAppStorePrivate.AppCategory
                                                          .INSTALLED);

            let appIds = [];
            for (let index in appInfos) {
                let appInfo = appInfos[index];

                if (appInfo.is_installed())
                    appIds.push(appInfo.get_application_id());
            }

            log("Returning " + appIds.length + " installed apps");
            invocation.return_value(GLib.Variant.new('(as)', [appIds]));
        }));
    },

    ListUpdatableAsync: function(params, invocation) {
        log("Listing updatable apps");
        this._app.appList.refresh(Lang.bind(this, function(error) {
            let success = (error == null);
            log("Refresh finished. Loading updatable apps");

            /* TODO: Handle refresh errors better */
            if (!success)
                invocation.return_value(GLib.Variant.new('(as)', [[]]));

            let appInfos = this._app.appList.loadCategory(EosAppStorePrivate.AppCategory
                                                          .INSTALLED);

            let appIds = [];
            for (let index in appInfos) {
                let appInfo = appInfos[index];
                if (appInfo.is_installed() && appInfo.is_updatable())
                    appIds.push(appInfo.get_application_id());
            }

            log("Returning " + appIds.length + " updatable apps");
            invocation.return_value(GLib.Variant.new('(as)', [appIds]));
        }));
    },

    ListUninstallableAsync: function(params, invocation) {
        log("Listing uninstallable apps");
        this._app.appList.refresh(Lang.bind(this, function(error) {
            let success = (error == null);

            /* TODO: Handle refresh errors better */
            if (!success)
                invocation.return_value(GLib.Variant.new('(as)', [[]]));

            log("Refresh finished. Loading uninstallable apps");

            let appInfos = this._app.appList.loadCategory(EosAppStorePrivate.AppCategory
                                                          .INSTALLED);

            let appIds = [];
            for (let index in appInfos) {
                let appInfo = appInfos[index];
                if (appInfo.is_installed() && appInfo.is_removable() &&
                    !appInfo.get_has_launcher())
                    appIds.push(appInfo.get_application_id());
            }

            log("Returning " + appIds.length + " uninstallable apps");
            invocation.return_value(GLib.Variant.new('(as)', [appIds]));
        }));
    },

    ListAvailable: function() {
        print("Stub!");
        return [];
    },

    RefreshAsync: function(params, invocation) {
        log("Refreshing apps");
        this._app.appList.refresh(Lang.bind(this, function(error) {
            let success = (error == null);
            log("Refresh finished. Success: " + success);
            invocation.return_value(GLib.Variant.new('(b)', [success]));
        }));
    },

    InstallAsync: function(params, invocation) {
        let [appId] = params;
        log("Installing: " + appId);

        this._app.appList.install(appId + ".desktop", Lang.bind(this, function(error) {
            let success = (error == null);
            log("Install finished. Success: " + success);
            invocation.return_value(GLib.Variant.new('(b)', [success]));
        }));
    },

    UninstallAsync: function(params, invocation) {
        let [appId] = params;
        log("Uninstalling: " + appId);

        this._app.appList.uninstall(appId + ".desktop", Lang.bind(this, function(error) {
            let success = (error == null);
            log("Uninstall finished. Success: " + success);
            invocation.return_value(GLib.Variant.new('(b)', [success]));
        }));
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
