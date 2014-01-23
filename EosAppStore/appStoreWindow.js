// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
//const Endless = imports.gi.Endless;
const Gdk = imports.gi.Gdk;
const GdkX11 = imports.gi.GdkX11;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const Pango = imports.gi.Pango;

const Lang = imports.lang;
const Signals = imports.signals;

const AppFrame = imports.appFrame;
const WeblinkFrame = imports.weblinkFrame;
const FolderFrame = imports.folderFrame;
const Path = imports.path;
const StoreModel = imports.storeModel;
const TwoLinesLabel = imports.twoLinesLabel;
const UIBuilder = imports.builder;
const WMInspect = imports.wmInspect;

const ANIMATION_TIME = (500 * 1000); // half a second

const PAGE_TRANSITION_MS = 500;

const SIDE_COMPONENT_ROLE = 'eos-side-component';

const AppStoreSizes = {
  // Note: must be listed in order of increasing screenWidth
  SVGA: { screenWidth:  800, windowWidth:  800 },
   XGA: { screenWidth: 1024, windowWidth:  800 },
  WXGA: { screenWidth: 1366, windowWidth: 1024 },
    HD: { screenWidth: 1920, windowWidth: 1366 },
};

const AppStoreWindow = new Lang.Class({
    Name: 'AppStoreWindow',
    Extends: Gtk.ApplicationWindow,
    Signals: {
        'visibility-changed': { param_types: [GObject.TYPE_BOOLEAN] },
        'back-clicked': { },
    },

    templateResource: '/com/endlessm/appstore/eos-app-store-main-window.ui',
    templateChildren: [
        'main-frame',
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
        'side-pane-apps-button',
        'side-pane-web-button',
        'side-pane-folder-button',
        'content-box',
        'header-bar-box',
        'header-bar-title-label',
        'header-bar-subtitle-label',
        'header-bar-installed-image',
        'header-icon',
        'close-button',
        'back-button',
    ],

    _init: function(app, storeModel) {
        this.parent({ application: app,
                        type_hint: Gdk.WindowTypeHint.DOCK,
                             type: Gtk.WindowType.TOPLEVEL,
                             role: SIDE_COMPONENT_ROLE
                    });

        this.initTemplate({ templateRoot: 'main-frame', bindChildren: true, connectSignals: true, });
        this.header_bar_subtitle_label = new TwoLinesLabel.TwoLinesLabel({ visible: true,
                                                                           xalign: 0,
                                                                           yalign: 0,
                                                                           ellipsize: Pango.EllipsizeMode.END,
                                                                           wrap: true,
                                                                           wrap_mode: Pango.WrapMode.WORD_CHAR });
        this.header_bar_subtitle_label.get_style_context().add_class('header-subtitle');
        this.header_bar_box.pack_start(this.header_bar_subtitle_label, false, true, 0);
        this.header_bar_box.reorder_child(this.header_bar_subtitle_label, 1);
        this.stick();
        this.set_resizable(false);
        this.set_decorated(false);
        // do not destroy, just hide
        this.connect('delete-event', Lang.bind(this, function() {
            this.toggle(false);
            return true;
        }));
        this.add(this.main_frame);

        this._loadSideImages();
        this._setLabelSizeGroup();

        // update position when workarea changes
        let screen = Gdk.Screen.get_default();
        this._monitorsChangedId = screen.connect('monitors-changed',
                       Lang.bind(this, this._onAvailableAreaChanged));
        this._monitorsSizeChangedId = screen.connect('size-changed',
                       Lang.bind(this, this._onAvailableAreaChanged));

        let visual = screen.get_rgba_visual();
        if (visual) {
            this.set_visual(visual);
        }

        this._updateGeometry();

        // the model that handles page changes
        this._storeModel = storeModel;
        this._storeModel.connect('page-changed', Lang.bind(this, this._onStorePageChanged));

        // the stack that holds the pages
        this._stack = null;
        this._createStackPages();

        // hide main window when clicking outside the store
        this._wmInspect = new WMInspect.WMInspect();
        this._activeWindowId = this._wmInspect.connect('active-window-changed',
                                                       Lang.bind(this, this._onActiveWindowChanged));
    },

    vfunc_destroy: function() {
        this.parent();

        let screen = Gdk.Screen.get_default();

        if (this._monitorsChangedId > 0) {
            screen.disconnect(this._monitorsChangedId);
            this._monitorsChangedId = 0;
        }

        if (this._monitorsSizeChangedId > 0) {
            screen.disconnect(this._monitorsSizeChangedId);
            this._monitorsSizeChangedId = 0;
        }

        if (this._activeWindowId > 0) {
            this._wmInspect.disconnect(this._activeWindowId);
            this._activeWindowId = 0;
        }
    },
    _getWorkArea: function() {
        let screen = Gdk.Screen.get_default();
        let monitor = screen.get_primary_monitor();
        let workArea = screen.get_monitor_workarea(monitor);

        return workArea;
    },

    _getResolution: function() {
        let workArea = this._getWorkArea();
        let resolution = null;

        // Find the largest defined resolution that does not exceed
        // the work area width
        for (let resolutionIdx in AppStoreSizes) {
            let res = AppStoreSizes[resolutionIdx];

            if (workArea.width >= res.screenWidth) {
                resolution = res;
            }
        }

        return resolution;
    },

    _getSize: function() {
        let workArea = this._getWorkArea();

        let resolution = this._getResolution();

        // If the work area is smaller than any defined resolution,
        // use the full size of the work area
        if (!resolution) {
            return [workArea.width, workArea.height];
        }

        return [resolution.windowWidth, workArea.height];
    },

    _updateGeometry: function() {
        let workArea = this._getWorkArea();
        let [width, height] = this._getSize();

        let geometry = { x: workArea.x,
                         y: workArea.y,
                         width: width,
                         height: height };


        this.move(geometry.x, geometry.y);
        this.set_size_request(geometry.width, geometry.height);
    },

    _createStackPages: function() {
        if (this._stack) {
            this.content_box.remove(this._stack);
        }

        // the stack that holds the pages
        this._stack = new Gtk.Stack();
        this._stack.set_transition_duration(PAGE_TRANSITION_MS);
        this._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT);
        this.content_box.add(this._stack);
        this._stack.show();

        // add the pages
        this._pages = [];
        this._pages[StoreModel.StorePage.APPS] = new AppFrame.AppFrame();
        this._stack.add_named(this._pages[StoreModel.StorePage.APPS], 'apps');
        this._pages[StoreModel.StorePage.WEB] = new WeblinkFrame.WeblinkFrame(this);
        this._stack.add_named(this._pages[StoreModel.StorePage.WEB], 'weblinks');
        this._pages[StoreModel.StorePage.FOLDERS] = new FolderFrame.FolderFrame();
        this._stack.add_named(this._pages[StoreModel.StorePage.FOLDERS], 'folders');
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

    _onActiveWindowChanged: function(wmInspect, activeXid) {
        let xid = this.get_window().get_xid();
        if (xid != activeXid) {
            this.hide();
        }
    },

    _onCloseClicked: function() {
        this.toggle(false);
    },

    _onBackClicked: function() {
        this.emit('back-clicked');
    },

    _onAppsClicked: function() {
        if (this.side_pane_apps_button.active) {
            this._storeModel.changePage(StoreModel.StorePage.APPS);
        }
    },

    _onWebClicked: function() {
        if (this.side_pane_web_button.active) {
            this._storeModel.changePage(StoreModel.StorePage.WEB);
        }
    },

    _onFolderClicked: function() {
        if (this.side_pane_folder_button.active) {
            this._storeModel.changePage(StoreModel.StorePage.FOLDERS);
        }
    },

    _setDefaultTitle: function() {
        let title = this.header_bar_title_label;

        switch (this._currentPage) {
            case StoreModel.StorePage.APPS:
                title.set_text(_("Install applications"));
                break;

            case StoreModel.StorePage.WEB:
                title.set_text(_("Install websites"));
                break;

            case StoreModel.StorePage.FOLDERS:
                title.set_text(_("Install folders"));
                break;
        }
    },

    _onStorePageChanged: function(model, newPage) {
        if (!this._pages[newPage]) {
            return;
        }

        this._pages.forEach(function(page) {
            page.hide();
        });

        let page = this._pages[newPage];
        this._currentPage = newPage;
        this.clearHeaderState();

        switch (this._currentPage) {
            case StoreModel.StorePage.APPS:
                this.side_pane_apps_button.active = true;
                break;

            case StoreModel.StorePage.WEB:
                this.side_pane_web_button.active = true;
                break;

            case StoreModel.StorePage.FOLDERS:
                this.side_pane_folder_button.active = true;
                break;
        }

        page.reset();
        page.show_all();
        this._stack.set_visible_child(page);
    },

    _onAvailableAreaChanged: function() {
        this._updateGeometry();
        this._createStackPages();
        this._onStorePageChanged(this._storeModel, this._currentPage);
    },

    toggle: function(reset, timestamp) {
        if (this.is_visible()) {
            this.hide();
        } else {
            let page = this._pages[this._currentPage];
            if (page && reset) {
                page.reset();
            }

            this.showPage(timestamp);
        }
    },

    showPage: function(timestamp) {
        this._updateGeometry();
        this.show();
        this.present_with_time(timestamp);
    },

    getExpectedWidth: function() {
        let [width, height] = this._getSize();

        return width;
    },

    clearHeaderState: function() {
        this.titleText = null;
        this.subtitleText = null;
        this.headerIcon = null;
        this.headerInstalledVisible = false;
        this.backButtonVisible = false;
    },

    set titleText(str) {
        if (str) {
            this.header_bar_title_label.set_text(str);
        }
        else {
            this._setDefaultTitle();
        }
    },

    set subtitleText(str) {
        if (str) {
            this.header_bar_subtitle_label.set_text(str);
            this.header_bar_subtitle_label.show();
        }
        else {
            this.header_bar_subtitle_label.hide();
        }
    },

    set headerIcon(str) {
        if (str) {
            this.header_icon.set_from_icon_name(str, Gtk.IconSize.DIALOG);
            this.header_icon.show();
        }
        else {
            this.header_icon.hide();
        }
    },

    set headerInstalledVisible(isVisible) {
        if (isVisible) {
            this.header_bar_installed_image.show();
        } else {
            this.header_bar_installed_image.hide();
        }
    },

    set backButtonVisible(isVisible) {
        if (isVisible) {
            this.back_button.show();
        }
        else {
            this.back_button.hide();
        }
    },
});
UIBuilder.bindTemplateChildren(AppStoreWindow.prototype);
