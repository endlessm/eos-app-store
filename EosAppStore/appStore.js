// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const Gettext = imports.gettext;
const Lang = imports.lang;
const Mainloop = imports.mainloop;
const Signals = imports.signals;
const _ = imports.gettext.gettext;

const AppStoreWindow = imports.appStoreWindow;
const AppStoreDBusService = imports.appStoreDBusService;
const Categories = imports.categories;
const Config = imports.config;
const Environment = imports.environment;
const Path = imports.path;
const ShellAppStore = imports.shellAppStore;

const APP_STORE_CSS = '/com/endlessm/appstore/eos-app-store.css';

const APP_STORE_NAME = 'com.endlessm.AppStore';

// Tear down the main window if it's been hidden for these many seconds
const CLEAR_TIMEOUT = 300;

// Quit the app store service if no main window is available after these
// many seconds
const QUIT_TIMEOUT = 15;

var AppStore = new Lang.Class({
    Name: 'AppStore',
    Extends: Gtk.Application,

    _init: function() {
        this._debugWindow = !!GLib.getenv('EOS_APP_STORE_DEBUG_WINDOW');

        this.parent({ application_id: APP_STORE_NAME,
                      flags: Gio.ApplicationFlags.IS_SERVICE,
                      inactivity_timeout: QUIT_TIMEOUT * 1000, });

        Environment.loadResources();

        this._clearId = 0;

        this._runningOperations = 0;

        this._dbusService = new AppStoreDBusService.AppStoreDBusService(this);
        this._dbusService.visibilityChanged(false);
    },

    vfunc_startup: function() {
        this.parent();

        // main style provider
        let provider = new Gtk.CssProvider();
        provider.load_from_resource(APP_STORE_CSS);
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);

        // The app store shell proxy
        this._shellProxy = new ShellAppStore.ShellAppStore();

        // No window by default
        this._mainWindow = null;
    },

    vfunc_activate: function() {
        this._createMainWindow();

        if (this.debugWindow) {
            this.showPage(Gdk.CURRENT_TIME, Categories.DEFAULT_APP_CATEGORY);
        }
    },

    _createMainWindow: function() {
        if (this._mainWindow == null) {
            this._mainWindow = new AppStoreWindow.AppStoreWindow(this);
            this._mainWindow.populate();
            this._mainWindow.connect('notify::visible',
                                     Lang.bind(this, this._onVisibilityChanged));
        }
    },

    get debugWindow() {
        return this._debugWindow;
    },

    get shellProxy() {
        return this._shellProxy;
    },

    get mainWindow() {
        return this._mainWindow;
    },

    show: function(timestamp, reset) {
        this._createMainWindow();
        if (reset) {
            this._mainWindow.resetCurrentPage();
        }
        this._mainWindow.show();
        this._mainWindow.present_with_time(timestamp);
    },

    hide: function() {
        if (this._mainWindow)
            this._mainWindow.hide();
    },

    hideIfVisible: function() {
        if (!this._debugWindow && this._mainWindow && this._mainWindow.is_visible()) {
            this._mainWindow.hide();
        }
    },

    showPage: function(timestamp, page) {
        this._createMainWindow();

        this._mainWindow.pageManager.showPage(page);
        this._mainWindow.show();
        this._mainWindow.present_with_time(timestamp);
    },

    _clearMainWindow: function() {
        this._clearId = 0;

        this._mainWindow.destroy();
        this._mainWindow = null;

        return false;
    },

    _onVisibilityChanged: function() {
        // Explicit name to prevent overriding of Gtk.Application fields/methods
        let is_window_visible = this._mainWindow.is_visible();

        this._dbusService.visibilityChanged(is_window_visible);

        // if the window stays hidden for a while and there are no running
        // operations (like an installation, upgrade, or removal) in progress,
        // we should destroy the window to free up resources. once the window
        // is gone, the inactivity timeout of Gio.Application will ensure that
        // the app store service goes away after a while as well.
        if (!is_window_visible && this._runningOperations == 0) {
            this._clearId =
                Mainloop.timeout_add_seconds(CLEAR_TIMEOUT,
                                             Lang.bind(this, this._clearMainWindow));
        }
        else {
            if (this._clearId != 0) {
                Mainloop.source_remove(this._clearId);
                this._clearId = 0;
            }
        }
    },

    pushRunningOperation: function() {
        this._runningOperations += 1;

        if (this._clearId) {
            Mainloop.source_remove(this._clearId);
            this._clearId = 0;
        }
    },

    popRunningOperation: function() {
        this._runningOperations -= 1;

        if (this._runningOperations < 0) {
            log("appStore.popRunningOperation() called without a previous call to " +
                "appStore.pushRunningOperation().");
            this._runningOperations = 0;
        }

        if (this._runningOperations == 0 && !this._mainWindow.is_visible()) {
            if (this._clearId != 0) {
                Mainloop.source_remove(this._clearId);
            }

            this._clearId =
                Mainloop.timeout_add_seconds(CLEAR_TIMEOUT, Lang.bind(this, this._clearMainWindow));
        }
    },
});
