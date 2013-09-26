// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const Gettext = imports.gettext;
const Lang = imports.lang;
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
    <arg type="u" direction="in" name="timestamp"/>
  </method>
  <method name="ShowPage">
    <arg type="s" direction="in" name="page"/>
    <arg type="u" direction="in" name="timestamp"/>
  </method>
  <property name="Visible" type="b" access="read"/>
</interface>;

const AppStore = new Lang.Class({
    Name: 'AppStore',
    Extends: Gtk.Application,

    _init: function(initialPage) {
        Gettext.bindtextdomain(Config.GETTEXT_DOMAIN, Path.LOCALE_DIR);
        Gettext.textdomain(Config.GETTEXT_DOMAIN);

        GLib.set_prgname('eos-app-store');
        GLib.set_application_name(_("Application Store"));

        this.parent({ application_id: APP_STORE_NAME, 
                      flags: Gio.ApplicationFlags.HANDLES_COMMAND_LINE });

        this._initialPage = initialPage;
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

        // the main window
        this._mainWindow = new AppStoreWindow.AppStoreWindow(this,
                                                             this._storeModel,
                                                             this._initialPage);
        this._mainWindow.connect('visibility-changed',
                                 Lang.bind(this, this._onVisibilityChanged));
    },

    vfunc_activate: function() {
        this._mainWindow.showPage(0);
    },

    vfunc_command_line: function(cmdline) {
        let noDefaultWindow = false;
        let initialPage = StoreModel.StorePage.APPS;
        let args = cmdline.get_arguments();
        for (let i = 0; i < args.length; i++) {
            let arg = args[i];

            if (arg == '--apps' || arg == '-a') {
                initialPage = StoreModel.StorePage.APPS;
                args.splice(i, 1);
                break;
            }

            if (arg == '--web-links' || arg == '-w') {
                initialPage = StoreModel.StorePage.WEB;
                args.splice(i, 1);
                break;
            }

            if (arg == '--folders' || arg == '-f') {
                initialPage = StoreModel.StorePage.FOLDERS;
                args.splice(i, 1);
                break;
            }

            if (arg == '--no-default-window' || arg == '-n') {
                noDefaultWindow = true;
                args.splice(i, 1);
            }

            log("Unrecognized argument '" + arg + "'\n" +
                "Usage: eos-app-store [--apps|--folders|--web-links]");
            return -1;
        }

        this._storeModel.changePage(initialPage);

        if (!noDefaultWindow) {
            this.activate();
        }

        return 0;
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

    set mainWindowTitle(str) {
        if (this._mainWindow != null) {
            this._mainWindow.titleText = str;
        }
    },

    set mainWindowSubtitle(str) {
        if (this._mainWindow != null) {
            this._mainWindow.subtitleText = str;
        }
    },

    Toggle: function(timestamp) {
        this._mainWindow.toggle(timestamp);
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

    _onVisibilityChanged: function(proxy, visible) {
        this.Visible = visible;

        let propChangedVariant = new GLib.Variant('(sa{sv}as)',
            [APP_STORE_IFACE, { 'Visible': new GLib.Variant('b', this.Visible) }, []]);

        Gio.DBus.session.emit_signal(null, APP_STORE_PATH,
                                     'org.freedesktop.DBus.Properties',
                                     'PropertiesChanged',
                                     propChangedVariant);
    }
});
