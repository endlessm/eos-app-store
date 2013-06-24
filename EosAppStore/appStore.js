const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;
const Lang = imports.lang;

const AppStoreWindow = imports.appStoreWindow;
const Path = imports.path;

const APP_STORE_NAME = 'com.endlessm.AppStore';

const AppStore = Lang.Class({
    Name: 'AppStore',
    Extends: Gtk.Application,

    _init: function() {
        this.parent({ application_id: APP_STORE_NAME, });
    },

    vfunc_startup: function() {
        this.parent();

        let resource = Gio.Resource.load(Path.RESOURCE_DIR + '/eos-app-store.gresource');
        resource._register();

        // main style provider
        let provider = new Gtk.CssProvider();
        provider.load_from_file(Gio.File.new_for_uri('resource:///com/endlessm/appstore/eos-app-store.css'));
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);

        // the main window
        this._mainWindow = new AppStoreWindow.AppStoreWindow(this);
    },

    vfunc_activate: function() {
        this._mainWindow.show();
        this._mainWindow.present();
    },

    get mainWindow() {
        return this._mainWindow;
    },
});
