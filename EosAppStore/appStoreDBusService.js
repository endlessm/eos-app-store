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
  '<method name="Update">' +
    '<arg type="s" direction="in" name="app_id"/>' +
    '<arg type="b" direction="out" name="success"/>' +
  '</method>' +
  '<property name="Visible" type="b" access="read"/>' +
'</interface></node>';

const AppStoreDBusService = new Lang.Class({
    Name: 'AppStoreDBusService',

    _init: function(app) {
        this._app = app;
        this.Visible = false;
        this._dbusImpl = Gio.DBusExportedObject.wrapJSObject(AppStoreDBusIface, this);
        this._dbusImpl.export(Gio.DBus.session, APP_STORE_PATH);
    },

    show: function(timestamp, reset) {
        log("App store show requested");
        this._app.show(timestamp, reset);
    },

    hide: function(timestamp) {
        log("App store hide requested");
        this._app.hide();
    },

    showPage: function(timestamp, page) {
        log("App store's " + page + " page requested");
        this._app.showPage(timestamp, page);
    },

    _genericListing: function(invocation, error, category, test_func) {
        let success = (error == null);
        log("Refresh finished. Loading apps");

        /* TODO: Handle refresh errors better */
        if (!success) {
            invocation.return_value(GLib.Variant.new('(as)', [[]]));
            return;
        }

        let appInfos = this._app.appList.loadCategory(category);

        let appIds = [];
        for (let index in appInfos) {
            let appInfo = appInfos[index];

            if (test_func(appInfo))
                appIds.push(appInfo.get_application_id());
        }

        log("Returning " + appIds.length + " apps matching criteria");
        invocation.return_value(GLib.Variant.new('(as)', [appIds]));
    },

    ListInstalledAsync: function(params, invocation) {
        log("Listing installed apps");

        this._app.appList.refresh(Lang.bind(this, function(error) {
            this._genericListing(invocation,
                                 error,
                                 EosAppStorePrivate.AppCategory.INSTALLED,
                                 function (appInfo) {
                                     return appInfo.is_installed();
                                 });
        }));
    },

    ListUpdatableAsync: function(params, invocation) {
        log("Listing updatable apps");

        this._app.appList.refresh(Lang.bind(this, function(error) {
            this._genericListing(invocation,
                                 error,
                                 EosAppStorePrivate.AppCategory.INSTALLED,
                                 function (appInfo) {
                                     return appInfo.is_installed() &&
                                            appInfo.is_updatable();
                                 });
        }));
    },

    ListUninstallableAsync: function(params, invocation) {
        log("Listing uninstallable apps");
        this._app.appList.refresh(Lang.bind(this, function(error) {
            this._genericListing(invocation,
                                 error,
                                 EosAppStorePrivate.AppCategory.INSTALLED,
                                 function (appInfo) {
                                     return appInfo.is_installed() &&
                                            appInfo.is_removable() &&
                                            !appInfo.get_has_launcher();
                                 });
        }));
    },

    ListAvailableAsync: function(params, invocation) {
        log("Listing available apps");
        this._app.appList.refresh(Lang.bind(this, function(error) {
            this._genericListing(invocation,
                                 error,
                                 EosAppStorePrivate.AppCategory.ALL,
                                 function (appInfo) {
                                     return appInfo.get_state() ==
                                            EosAppStorePrivate.AppState.AVAILABLE;
                                 });
        }));
    },

    RefreshAsync: function(params, invocation) {
        log("Refreshing apps");
        this._app.appList.refresh(Lang.bind(this, function(error) {
            let success = (error == null);
            log("Refresh finished. Success: " + success);
            invocation.return_value(GLib.Variant.new('(b)', [success]));
        }));
    },

    _refresh: function(callback) {
        this._app.appList.refresh(callback);
    },

    InstallAsync: function(params, invocation) {
        let [appId] = params;

        this._refresh(Lang.bind(this, function(error) {
            log("Refreshing before install");
            if (error != null) {
                invocation.return_value(GLib.Variant.new('(b)', [false]));
                return;
            }

            log("Installing: " + appId);
            this._app.appList.install(appId + ".desktop", Lang.bind(this, function(error) {
                let success = (error == null);
                log("Install finished. Success: " + success);
                invocation.return_value(GLib.Variant.new('(b)', [success]));
            }));
        }));
    },

    UninstallAsync: function(params, invocation) {
        let [appId] = params;

        this._refresh(Lang.bind(this, function(error) {
            log("Refreshing before install");
            if (error != null) {
                invocation.return_value(GLib.Variant.new('(b)', [false]));
                return;
            }

            log("Uninstalling: " + appId);
            this._app.appList.uninstall(appId + ".desktop", Lang.bind(this, function(error) {
                let success = (error == null);
                log("Uninstall finished. Success: " + success);
                invocation.return_value(GLib.Variant.new('(b)', [success]));
            }));
        }));
    },

    UpdateAsync: function(params, invocation) {
        let [appId] = params;

        this._refresh(Lang.bind(this, function(error) {
            log("Refreshing before install");
            if (error != null) {
                invocation.return_value(GLib.Variant.new('(b)', [false]));
                return;
            }

            log("Installing: " + appId);
            this._app.appList.updateApp(appId + ".desktop", Lang.bind(this, function(error) {
                let success = (error == null);
                log("Update finished. Success: " + success);
                invocation.return_value(GLib.Variant.new('(b)', [success]));
            }));
        }));
    },

    visibilityChanged: function(is_visible) {
        this.Visible = is_visible;

        let propChangedVariant = new GLib.Variant('(sa{sv}as)',
            [APP_STORE_IFACE, { 'Visible': new GLib.Variant('b', this.Visible) }, []]);

        Gio.DBus.session.emit_signal(null, APP_STORE_PATH,
                                     'org.freedesktop.DBus.Properties',
                                     'PropertiesChanged',
                                     propChangedVariant);
    }
});
