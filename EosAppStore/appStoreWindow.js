// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
//const Endless = imports.gi.Endless;
const Gdk = imports.gi.Gdk;
const GdkX11 = imports.gi.GdkX11;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const PLib = imports.gi.PLib;

const Lang = imports.lang;
const Signals = imports.signals;

const AppFrame = imports.appFrame;
const WeblinkFrame = imports.weblinkFrame;
const FolderFrame = imports.folderFrame;
const FrameClock = imports.frameClock;
const Path = imports.path;
const StoreModel = imports.storeModel;
const UIBuilder = imports.builder;

const ANIMATION_TIME = (500 * 1000); // half a second

const PAGE_TRANSITION_MS = 500;

const AppStoreSizes = {
  // Note: must be listed in order of increasing screenWidth
  SVGA: { screenWidth:  800, windowWidth:  800 },
   XGA: { screenWidth: 1024, windowWidth:  800 },
  WXGA: { screenWidth: 1366, windowWidth: 1024 },
    HD: { screenWidth: 1920, windowWidth: 1366 },
};

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

    _getResolution: function() {
        let workarea = this._getWorkarea();
        let resolution = null;

        // Find the largest defined resolution that does not exceed
        // the work area width
        for (let i in AppStoreSizes) {
            let res = AppStoreSizes[i];

            if (workarea.width >= res.screenWidth) {
                resolution = res;
            }
        }

        return resolution;
    },

    _getSize: function() {
        let workarea = this._getWorkarea();

        let resolution = this._getResolution();

        // If the work area is smaller than any defined resolution,
        // use the full size of the work area
        if (!resolution) {
            return [workarea.width, workarea.height];
        }

        return [resolution.windowWidth, workarea.height];
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

    get resolution() {
        return this._getResolution();
    },

    get expectedWidth() {
        let [width, height] = this._getSize();

        return width;
    },
});
Signals.addSignalMethods(AppStoreSlider.prototype);

const AppStoreWindow = new Lang.Class({
    Name: 'AppStoreWindow',
    Extends: Gtk.ApplicationWindow,
    Signals: {
        'visibility-changed': { param_types: [GObject.TYPE_BOOLEAN] },
    },

    templateResource: '/com/endlessm/appstore/eos-app-store-main-window.ui',
    templateChildren: [
        'main-box',
        'side-pane-apps-image',
        'side-pane-web-image',
        'side-pane-folder-image',
        'side-pane-apps-label',
        'side-pane-web-label',
        'side-pane-folder-label',
        'side-pane-apps-label-bold',
        'side-pane-web-label-bold',
        'side-pane-folder-label-bold',
        'content-box',
        'header-bar-title-label',
        'close-button',
    ],

    _init: function(app, storeModel, initialPage) {
        this.parent({ application: app,
                        type_hint: Gdk.WindowTypeHint.DOCK,
                             type: Gtk.WindowType.TOPLEVEL,
                    });

        this.initTemplate({ templateRoot: 'main-box', bindChildren: true, connectSignals: true, });
        this.stick();
        this.set_decorated(false);
        // do not destroy, just hide
        this.connect('delete-event', Lang.bind(this, function() {
            this.toggle();
            return true;
        }));
        // bug: https://bugzilla.gnome.org/show_bug.cgi?id=703154
        this.connect('realize', Lang.bind(this, function() { this.opacity = 0.95; }));
        this.add(this.main_box);

        this._loadSideImages();
        this._setLabelSizeGroup();

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

        // the model that handles page changes
        this._storeModel = storeModel;
        this._storeModel.connect('page-changed', Lang.bind(this, this._onStorePageChanged));

        // the stack that holds the pages
        this._stack = new PLib.Stack();
        this._stack.set_transition_duration(PAGE_TRANSITION_MS);
        this._stack.set_transition_type(PLib.StackTransitionType.SLIDE_RIGHT);
        this.content_box.add(this._stack);
        this._stack.show();

        // add the pages
        this._pages = {};
        this._pages.apps = new AppFrame.AppFrame();
        this._stack.add_named(this._pages.apps, 'apps');
        this._pages.weblinks = new WeblinkFrame.WeblinkFrame(this);
        this._stack.add_named(this._pages.weblinks, 'weblinks');
        this._pages.folders = new FolderFrame.FolderFrame();
        this._stack.add_named(this._pages.folders, 'folders');

        // switch to the 'Applications' page
        this._onStorePageChanged(this._storeModel, StoreModel.StorePage.APPS);
    },

    _loadSideImages: function() {
        let resources = { side_pane_apps_image: 'icon_apps-symbolic.svg',
                          side_pane_web_image: 'icon_website-symbolic.svg',
                          side_pane_folder_image: 'icon_folder-symbolic.svg' };

        for (let object in resources) {
            let iconName = resources[object];
            let file = Gio.File.new_for_path(Path.ICONS_DIR + '/' + iconName);
            let icon = new Gio.FileIcon({ file: file });
            this[object].gicon = icon;
        }
    },

    _setLabelSizeGroup: function() {
        let labels = ['side_pane_apps_label',
                      'side_pane_web_label',
                      'side_pane_folder_label',
                      'side_pane_apps_label_bold',
                      'side_pane_web_label_bold',
                      'side_pane_folder_label_bold'];

        let sizeGroup = new Gtk.SizeGroup();
        for (let idx in labels) {
            let object = labels[idx];
            sizeGroup.add_widget(this[object]);
        }
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
        let stack = this._stack;
        let page = null;

        for (let p in this._pages) {
            this._pages[p].hide();
        }

        switch (newPage) {
            case StoreModel.StorePage.APPS:
                title.set_text(_("Install Applications"));
                page = this._pages.apps;
                break;

            case StoreModel.StorePage.WEB:
                title.set_text(_("Install Websites"));
                page = this._pages.weblinks;
                break;

            case StoreModel.StorePage.FOLDERS:
                title.set_text(_("Folders"));
                page = this._pages.folders;
                break;
        }

        if (page) {
            page.reset();
            page.show_all();
            stack.set_visible_child(page);
        }
    },

    _onMonitorsChanged: function() {
        this._animator.setInitialValue();
    },

    _onVisibilityChanged: function() {
        this.emit('visibility-changed', this._animator.showing);
    },

    getVisible: function() {
        return this._animator.showing;
    },

    toggle: function(timestamp) {
        if (this._animator.showing) {
            this._animator.slideOut();
        } else {
            this.showPage(timestamp);
        }
    },

    showPage: function(timestamp) {
        this._animator.slideIn();
        this.present_with_time(timestamp);
    },

    getExpectedWidth: function() {
        return this._animator.expectedWidth;
    },
});
UIBuilder.bindTemplateChildren(AppStoreWindow.prototype);
