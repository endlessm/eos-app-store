// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const Gettext = imports.gettext;
const Lang = imports.lang;
const Signals = imports.signals;
const _ = imports.gettext.gettext;

const AppStoreWindow = imports.appStoreWindow;
const Config = imports.config;
const Path = imports.path;
const StoreModel = imports.storeModel;

const APP_STORE_NAME = 'com.endlessm.AppStore';

const AppStore = new Lang.Class({
    Name: 'AppStore',
    Extends: Gtk.Application,

    _init: function() {
        Gettext.bindtextdomain(Config.GETTEXT_DOMAIN, Path.LOCALE_DIR);
        Gettext.textdomain(Config.GETTEXT_DOMAIN);

        GLib.set_prgname('eos-app-store');
        GLib.set_application_name(_("Application Store"));

        this.parent({ application_id: APP_STORE_NAME, });

        this._storeModel = new StoreModel.StoreModel();
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
        this._mainWindow = new AppStoreWindow.AppStoreWindow(this, this._storeModel);
    },

    vfunc_activate: function() {
        this._mainWindow.toggle();
    },

    get mainWindow() {
        return this._mainWindow;
    },
});
