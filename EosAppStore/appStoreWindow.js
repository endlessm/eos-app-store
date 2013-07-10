// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
//const Endless = imports.gi.Endless;
const Gdk = imports.gi.Gdk;
const GdkX11 = imports.gi.GdkX11;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const Lang = imports.lang;
const Signals = imports.signals;

const FrameClock = imports.frameClock;
const StoreModel = imports.storeModel;
const UIBuilder = imports.builder;

const APP_STORE_WIDTH = 512;
const MAX_FRACTION_OF_DISPLAY_WIDTH = 0.65;
const ANIMATION_TIME = (500 * 1000); // half a second

const AppStoreSlider = new Lang.Class({
    Name: 'AppStoreSlider',
    Extends: FrameClock.FrameClockAnimator,

    _init: function(widget) {
        this._showing = false;
        this.parent(widget, ANIMATION_TIME);
    },

    _getX: function(forVisibility) {
        let [width, height] = this._getSize();
        let workarea = this._getWorkarea();
        let x = workarea.x - width;

        if (forVisibility) {
            x += width;
        }

        return x;
    },

    _getInitialValue: function() {
        return this._getX(!this.showing);
    },

    setValue: function(newX) {
        let [, oldY] = this._widget.get_position();
        this._widget.move(newX, oldY);
    },

    _getWorkarea: function() {
        let screen = Gdk.Screen.get_default();
        let monitor = screen.get_primary_monitor();
        let workarea = screen.get_monitor_workarea(monitor);

        return workarea;
    },

    _getSize: function() {
        let workarea = this._getWorkarea();
        let maxWidth = workarea.width * MAX_FRACTION_OF_DISPLAY_WIDTH;
        return [Math.max(APP_STORE_WIDTH, maxWidth), workarea.height];
    },

    _updateGeometry: function() {
        let workarea = this._getWorkarea();
        let [width, height] = this._getSize();
        let x = this._getX(this.showing);

        let geometry = { x: x,
                         y: workarea.y,
                         width: width,
                         height: height };

        this._widget.move(geometry.x, geometry.y);
        this._widget.set_size_request(geometry.width, geometry.height);
    },

    setInitialValue: function() {
        this.stop();
        this._updateGeometry();
    },

    slideIn: function() {
        if (this.showing) {
            return;
        }

        this.setInitialValue();
        this._widget.show();

        this.showing = true;
        this.start(this._getX(true));
    },

    slideOut: function() {
        if (!this.showing) {
            return;
        }

        this.showing = false;
        this.start(this._getX(false), Lang.bind(this,
            function() {
                this._widget.hide();
            }));
    },

    set showing(value) {
        this._showing = value;
        this.emit('visibility-changed');
    },

    get showing() {
        return this._showing;
    },
});
Signals.addSignalMethods(AppStoreSlider.prototype);

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
                        type_hint: Gdk.WindowTypeHint.DOCK,
                             type: Gtk.WindowType.TOPLEVEL,
                    });

        this.initTemplate({ templateRoot: 'main-box', bindChildren: true, connectSignals: true, });
        this.stick();
        this.set_default_size(720, -1);
        this.set_decorated(false);
        // do not destroy, just hide
        this.connect('delete-event', Lang.bind(this, function() {
            this.toggle();
            return true;
        }));
        // bug: https://bugzilla.gnome.org/show_bug.cgi?id=703154
        this.connect('realize', Lang.bind(this, function() { this.opacity = 0.95; }));
        this.add(this.main_box);

        // update position when workarea changes
        let screen = Gdk.Screen.get_default();
        screen.connect('monitors-changed',
                       Lang.bind(this, this._onMonitorsChanged));

        let visual = screen.get_rgba_visual();
        if (visual) {
            this.set_visual(visual);
        }

        // initialize animator
        this._animator = new AppStoreSlider(this);
        this._animator.connect('visibility-changed', Lang.bind(this, this._onVisibilityChanged));
        this._animator.setInitialValue();
        this._animator.showing = false;

        this._storeModel = storeModel;
        this._storeModel.connect('page-changed', Lang.bind(this, this._onStorePageChanged));
        this._onStorePageChanged(this._storeModel, StoreModel.StorePage.APPS);
    },

    _onCloseClicked: function() {
        this.toggle();
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
                title.set_text(_("INSTALL APPLICATIONS"));
                desc.set_text(_("A list of many free applications you can install and update"));
                break;

            case StoreModel.StorePage.WEB:
                title.set_text(_("WEB"));
                desc.set_text(_("A descriptive label for the Web section"));
                break;

            case StoreModel.StorePage.FOLDERS:
                title.set_text(_("FOLDERS"));
                desc.set_text(_("A descriptive label for the Folders section"));
                break;
        }
    },

    _onMonitorsChanged: function() {
        this._animator.setInitialValue();
    },

    _onVisibilityChanged: function() {
    },

    getVisible: function() {
        return this._animator.showing;
    },

    toggle: function() {
        if (this._animator.showing) {
            this._animator.slideOut();
        }
        else {
            this._animator.slideIn();
            this.present();
        }
    },
});

UIBuilder.bindTemplateChildren(AppStoreWindow.prototype);
