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
const UIBuilder = imports.builder;
const WMInspect = imports.wmInspect;

const ANIMATION_TIME = (500 * 1000); // half a second

const PAGE_TRANSITION_MS = 250;

const SIDE_COMPONENT_ROLE = 'eos-side-component';

const AppStoreSizes = {
    // Note: must be listed in order of increasing screenWidth.
    // Window widths are chosen by design to match a specific
    // number of columns of tiles on the application grid.
    // Higher resolution thresholds include compensation for 5% overscan
    // on either side, plus some additional margin.
    // Pick the highest resolution for which the
    // threshold is met, and use the specified window and sidebar width,
    // truncating if necessary to the actual screen width.
    // Table screen widths are the nominal screen widths
    // for each resolution, useful as fixed constants
    // (whereas the threshold and window widths may be
    // adjusted as necessary).
    // For any screen smaller than 1024 wide (even XGA w/ overscan),
    // use a window width of 800 (or the full screen width if less
    // than 800), since we don't handle narrower windows well.
    VGA:  { screenWidth:  640, thresholdWidth:    0, windowWidth:  800,
            sidebarWidth: 186 },
    SVGA: { screenWidth:  800, thresholdWidth:  800, windowWidth:  800,
            sidebarWidth: 186 },
    XGA:  { screenWidth: 1024, thresholdWidth: 1024, windowWidth: 1024,
            sidebarWidth: 215 },
    WXGA: { screenWidth: 1366, thresholdWidth: 1200, windowWidth: 1024,
            sidebarWidth: 215 },
    HD:   { screenWidth: 1920, thresholdWidth: 1700, windowWidth: 1414,
            sidebarWidth: 215 }
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
        'sidebar-frame',
        'side-pane-box',
        'content-box',
        'header-bar-box',
        'header-bar-title-label',
        'header-bar-subtitle-label',
        'header-icon',
        'close-button',
        'back-button',
    ],

    _init: function(app) {
        this.parent({ application: app,
                        type_hint: Gdk.WindowTypeHint.DOCK,
                             type: Gtk.WindowType.TOPLEVEL,
                             role: SIDE_COMPONENT_ROLE
                    });

        this.initTemplate({ templateRoot: 'main-frame', bindChildren: true, connectSignals: true, });
        this.stick();
        this.set_decorated(false);
        this.get_style_context().add_class('main-window');

        // do not destroy, just hide
        this.connect('delete-event', Lang.bind(this, function() {
            this.hide();
            return true;
        }));
        this.add(this.main_frame);

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
            if (workArea.width >= res.thresholdWidth) {
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

        // If the selected resolution specifies a window width
        // that exceeds the work area, truncate it as necessary
        return [Math.min(workArea.width, resolution.windowWidth),
                workArea.height,
                resolution.sidebarWidth];
    },

    _updateGeometry: function() {
        let workArea = this._getWorkArea();
        let [width, height, sidebarWidth] = this._getSize();
        let x = workArea.x;

        if (this.get_direction() == Gtk.TextDirection.RTL) {
            x += workArea.width - width;
        }

        let geometry = { x: x,
                         y: workArea.y,
                         width: width,
                         height: height };

        this.move(geometry.x, geometry.y);
        this.resize(geometry.width, geometry.height);

        this.sidebar_frame.width_request = sidebarWidth;
    },

    _createStackPages: function() {
        if (this._stack) {
            this.content_box.remove(this._stack);
        }

        // the stack that holds the pages
        this._stack = new Gtk.Stack();
        this._stack.connect('notify::visible-child-name',
                            Lang.bind(this, this._onStorePageChanged));
        this.side_pane_box.stack = this._stack;
        this.content_box.add(this._stack);
        this._stack.show();

        let appFrame = new AppFrame.AppBroker(this);
        let categories = appFrame.categories;

        categories.forEach(Lang.bind(this, function(category) {
            this._stack.add_titled(category.widget, category.name, category.label);
        }));
        this._stack.add_titled(new WeblinkFrame.WeblinkFrame(this), 'weblinks', _("Websites"));
        this._stack.add_titled(new FolderFrame.FolderFrame(), 'folders', _("Folders"));
    },

    _onActiveWindowChanged: function(wmInspect, activeWindow) {
        // try to match the own window first
        let activeXid = activeWindow.get_xid();
        let xid = this.get_window().get_xid();

        if (xid == activeXid) {
            return;
        }

        // try to match transient windows
        let transientWindow = activeWindow.get_transient();
        let transientXid = 0;

        if (transientWindow != null) {
            transientXid = transientWindow.get_xid();
        }

        if (xid == transientXid) {
            return;
        }

        // no matches - hide our own window
        this.hide();
    },

    _onCloseClicked: function() {
        this.hide();
    },

    _onBackClicked: function() {
        this.emit('back-clicked');
    },

    _setDefaultTitle: function() {
        let title = this.header_bar_title_label;
        title.set_text(this._stack.get_visible_child().title);
    },

    _onStorePageChanged: function() {
        let page = this._stack.visible_child;
        this.clearHeaderState();

        page.reset();
    },

    _onAvailableAreaChanged: function() {
        this._updateGeometry();
        this._createStackPages();
        this._onStorePageChanged();
    },

    doShow: function(reset, timestamp) {
        let page = this._stack.get_visible_child();
        if (page && reset) {
            page.reset();
        }

        this.showPage(timestamp);
    },

    changePage: function(page) {
        this._stack.visible_child_name = page;
    },

    showPage: function(timestamp) {
        this._updateGeometry();
        this.show();
        this.present_with_time(timestamp);
    },

    getExpectedWidth: function() {
        let [width, height, sidebarWidth] = this._getSize();

        return width;
    },

    clearHeaderState: function() {
        this.titleText = null;
        this.subtitleText = null;
        this.headerIcon = null;
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
