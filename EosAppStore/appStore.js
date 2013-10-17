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
const AppStoreWindow = imports.appStoreWindow;
const Config = imports.config;
const Path = imports.path;
const ShellAppStore = imports.shellAppStore;
const StoreModel = imports.storeModel;

const APP_STORE_CSS = 'resource:///com/endlessm/appstore/eos-app-store.css';

const APP_STORE_NAME = 'com.endlessm.AppStore';
const APP_STORE_PATH = '/com/endlessm/AppStore';
const APP_STORE_IFACE = 'com.endlessm.AppStore';

const AppStoreIface = <interface name={APP_STORE_NAME}>
  <method name="Toggle">
    <arg type="b" direction="in" name="reset"/>
    <arg type="u" direction="in" name="timestamp"/>
  </method>
  <method name="ShowPage">
    <arg type="s" direction="in" name="page"/>
    <arg type="u" direction="in" name="timestamp"/>
  </method>
  <property name="Visible" type="b" access="read"/>
</interface>;

const CLEAR_TIMEOUT = 15000;

const AppStore = new Lang.Class({
    Name: 'AppStore',
    Extends: Gtk.Application,

    _init: function() {
        this.parent({     application_id: APP_STORE_NAME,
                                   flags: Gio.ApplicationFlags.IS_SERVICE,
                      inactivity_timeout: CLEAR_TIMEOUT, });

        this._storeModel = new StoreModel.StoreModel();
        this.Visible = false;

        this._dbusImpl = Gio.DBusExportedObject.wrapJSObject(AppStoreIface, this);
        this._dbusImpl.export(Gio.DBus.session, APP_STORE_PATH);
    },

    vfunc_startup: function() {
        this.parent();

        let resource = Gio.Resource.load(Path.RESOURCE_DIR + '/eos-app-store.gresource');
        resource._register();

        // main style provider
        let provider = new Gtk.CssProvider();
        provider.load_from_file(Gio.File.new_for_uri(APP_STORE_CSS));
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);

        // the app store shell proxy
        this._shellProxy = new ShellAppStore.ShellAppStore();

        // the backing app list model
        this._appModel = new AppListModel.StoreModel();
    },

    vfunc_activate: function() {
        this._createMainWindow();
    },

    _createMainWindow: function() {
        if (this._mainWindow == null) {
            this._mainWindow = new AppStoreWindow.AppStoreWindow(this,
                                                                 this._storeModel);
            this._mainWindow.connect('visibility-changed',
                                     Lang.bind(this, this._onVisibilityChanged));
        }
    }

    get appModel() {
        return this._appModel;
    },

    get shellProxy() {
        return this._shellProxy;
    },

    get mainWindow() {
        this._createMainWindow();
        return this._mainWindow;
    },

    get mainWindowWidth() {
        if (this._mainWindow != null) {
            return this._mainWindow.getExpectedWidth();
        }

        return AppStoreWindow.AppStoreSizes.SVGA.windowWidth;
    },

    Toggle: function(reset, timestamp) {
        this._mainWindow.toggle(reset, timestamp);
    },

    ShowPage: function(page, timestamp) {
        let valid = true;
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

    _onVisibilityChanged: function(proxy, visible) {
        this.Visible = visible;

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
                Mainloop.timeout_add(CLEAR_TIMEOUT, Lang.bind(this, this._clearMainWindow));
        }
        else {
            if (this._clearId != 0) {
                Mainloop.source_remove(this._clearId);
                this._clearId = 0;
            }
        }
    }
});
