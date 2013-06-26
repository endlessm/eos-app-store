const Gdk = imports.gi.Gdk;
const GdkX11 = imports.gi.GdkX11;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const Lang = imports.lang;
const Signals = imports.signals;

const UIBuilder = imports.builder;
const FrameClock = imports.frameClock;
const StoreModel = imports.storeModel;

const AppStoreWindow = new Lang.Class({
    Name: 'AppStoreWindow',
    Extends: Gtk.ApplicationWindow,

    templateResource: '/com/endlessm/appstore/eos-app-store-main-window.ui',
    templateChildren: [
        'main-box',
        'side-pane-apps-button',
        'side-pane-web-button',
        'side-pane-folder-button',
        'content-box',
        'header-bar-title-label',
        'header-bar-description-label',
        'close-button',
    ],

    _init: function(app, storeModel) {
        this.parent({ application: app,
                             type: Gtk.WindowType.TOPLEVEL,
                    });

        this.initTemplate({ templateRoot: 'main-box', bindChildren: true, connectSignals: true, });
        this.set_default_size(600, 400);
        this.add(this.main_box);

        this._storeModel = storeModel;
        this._storeModel.connect('page-changed', Lang.bind(this, this._onStorePageChanged));
        this._onStorePageChanged(this._storeModel, StoreModel.StorePage.APPS);
    },

    _onCloseClicked: function() {
        this.hide();
    },

    _onAppsClicked: function() {
        this._storeModel.changePage(StoreModel.StorePage.APPS);
    },

    _onWebClicked: function() {
        this._storeModel.changePage(StoreModel.StorePage.WEB);
    },

    _onFolderClicked: function() {
        this._storeModel.changePage(StoreModel.StorePage.FOLDERS);
    },

    _onStorePageChanged: function(model, newPage) {
        let title = this.header_bar_title_label;
        let desc = this.header_bar_description_label;

        switch (newPage) {
            case StoreModel.StorePage.APPS:
                title.set_text("INSTALL APPLICATIONS");
                desc.set_text("A list of many free applications you can install and update");
                break;

            case StoreModel.StorePage.WEB:
                title.set_text("WEB");
                desc.set_text("A descriptive label for the Web section");
                break;

            case StoreModel.StorePage.FOLDERS:
                title.set_text("FOLDERS");
                desc.set_text("A descriptive label for the Folders section");
                break;
        }
    },
});

UIBuilder.bindChildrenById(AppStoreWindow.prototype);
