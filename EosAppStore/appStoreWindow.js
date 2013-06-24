const Gdk = imports.gi.Gdk;
const GdkX11 = imports.gi.GdkX11;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;
const Lang = imports.lang;
const Signals = imports.signals;
const UIBuilder = imports.builder;

const FrameClock = imports.frameClock;

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

    _init: function(app) {
        this.parent({ application: app,
                             type: Gtk.WindowType.TOPLEVEL,
                    });

        this.initTemplate({ templateRoot: 'main-box', bindChildren: true, connectSignals: true, });
        this.set_default_size(600, 400);
        this.add(this.main_box);
    },

    _onCloseClicked: function() {
        this.hide();
    },
});

UIBuilder.bindChildrenById(AppStoreWindow.prototype);
