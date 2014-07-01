// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const Gettext = imports.gettext;
const Lang = imports.lang;
const Mainloop = imports.mainloop;
const Signals = imports.signals;
const _ = imports.gettext.gettext;

const AppListModel = imports.appListModel;
const AppManager = imports.appManager;
const AppStoreWindow = imports.appStoreWindow;
const Config = imports.config;
const Environment = imports.environment;
const Path = imports.path;
const ShellAppStore = imports.shellAppStore;
const StoreModel = imports.storeModel;

const APP_STORE_CSS = 'resource:///com/endlessm/appstore/eos-app-store.css';

const APP_STORE_NAME = 'com.endlessm.AppStore';
const APP_STORE_PATH = '/com/endlessm/AppStore';
const APP_STORE_IFACE = 'com.endlessm.AppStore';

const AppStoreIface = '<node><interface name="com.endlessm.AppStore">' +
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

// Tear down the main window if it's been hidden for these many seconds
const CLEAR_TIMEOUT = 300;

// Quit the app store service if no main window is available after these
// many seconds
const QUIT_TIMEOUT = 15;

const AppStore = new Lang.Class({
    Name: 'AppStore',
    Extends: Gtk.Application,

    _init: function() {
        this.parent({ application_id: APP_STORE_NAME,
                      flags: Gio.ApplicationFlags.IS_SERVICE,
                      inactivity_timeout: QUIT_TIMEOUT * 1000, });

        Environment.loadResources();

        this._storeModel = new StoreModel.StoreModel();
        this.Visible = false;
        this._clearId = 0;

        this._dbusImpl = Gio.DBusExportedObject.wrapJSObject(AppStoreIface, this);
        this._dbusImpl.export(Gio.DBus.session, APP_STORE_PATH);
    },

    vfunc_startup: function() {
        this.parent();

        // main style provider
        let provider = new Gtk.CssProvider();
        provider.load_from_file(Gio.File.new_for_uri(APP_STORE_CSS));
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);

        // the app store shell proxy
        this._shellProxy = new ShellAppStore.ShellAppStore();

        // the app manager proxy
        this._appManager = new AppManager.AppManager();
        this._appManager.proxy.RefreshRemote();

        // the backing app list model
        this._appModel = new AppListModel.StoreModel();

        // no window by default
        this._mainWindow = null;
    },

    vfunc_activate: function() {
        this._createMainWindow();
    },

    _createMainWindow: function() {
        if (this._mainWindow == null) {
            this._mainWindow = new AppStoreWindow.AppStoreWindow(this,
                                                                 this._storeModel);
            this._mainWindow.connect('notify::visible',
                                     Lang.bind(this, this._onVisibilityChanged));

            // set initial page
            this._storeModel.changePage(StoreModel.StorePage.APPS);
        }
    },

    get appModel() {
        return this._appModel;
    },

    get shellProxy() {
        return this._shellProxy;
    },

    get mainWindow() {
        return this._mainWindow;
    },

    get mainWindowWidth() {
        if (this._mainWindow != null) {
            return this._mainWindow.getExpectedWidth();
        }

        return AppStoreWindow.AppStoreSizes.SVGA.windowWidth;
    },

    show: function(timestamp, reset) {
        this._createMainWindow();
        this._mainWindow.doShow(reset, timestamp);
    },

    hide: function(timestamp) {
        if (this._mainWindow)
            this._mainWindow.hide();
    },

    showPage: function(timestamp, page) {
        this._createMainWindow();

        if (page == 'apps') {
            this._storeModel.changePage(StoreModel.StorePage.APPS);
        } else if (page == 'folders') {
            this._storeModel.changePage(StoreModel.StorePage.FOLDERS);
        } else if (page == 'web') {
            this._storeModel.changePage(StoreModel.StorePage.WEB);
        } else {
            log("Unrecognized page '" + page + "'");
        }

        this._mainWindow.showPage(timestamp);
    },

    _clearMainWindow: function() {
        this._clearId = 0;

        this._mainWindow.destroy();
        this._mainWindow = null;

        return false;
    },

    _onVisibilityChanged: function() {
        this.Visible = this._mainWindow.is_visible();

        let propChangedVariant = new GLib.Variant('(sa{sv}as)',
            [APP_STORE_IFACE, { 'Visible': new GLib.Variant('b', this.Visible) }, []]);

        Gio.DBus.session.emit_signal(null, APP_STORE_PATH,
                                     'org.freedesktop.DBus.Properties',
                                     'PropertiesChanged',
                                     propChangedVariant);

        // if the window stays hidden for a while, we should destroy it to
        // free up resources. once the window is gone, the inactivity timeout
        // of Gio.Application will ensure that the app store service goes away
        // after a while.
        if (!this.Visible) {
            this._clearId =
                Mainloop.timeout_add_seconds(CLEAR_TIMEOUT, Lang.bind(this, this._clearMainWindow));
        }
        else {
            if (this._clearId != 0) {
                Mainloop.source_remove(this._clearId);
                this._clearId = 0;
            }
        }
    }
});
