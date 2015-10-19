// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const AppInfoBox = imports.appInfoBox;
const AppInstalledBox = imports.appInstalledBox;
const AppStorePages = imports.appStorePages;
const Builder = imports.builder;
const Categories = imports.categories;
const Lang = imports.lang;
const Separator = imports.separator;

const APP_TRANSITION_MS = 500;

const CELL_DEFAULT_SIZE = 180;
const CELL_DEFAULT_SPACING = 15;

const CONTENT_PAGE = 'content';
const SPINNER_PAGE = 'spinner';

const AppFrame = new Lang.Class({
    Name: 'AppFrame',
    Extends: Gtk.Frame,

    _init: function(category) {
        this.parent();

        this.get_style_context().add_class('app-frame');

        this._stack = new Gtk.Stack({ transition_duration: APP_TRANSITION_MS,
                                      transition_type: Gtk.StackTransitionType.SLIDE_RIGHT,
                                      hexpand: true,
                                      vexpand: true });
        this._stack.connect('notify::visible-child-name', Lang.bind(this, this._onPageChanged));
        this.add(this._stack);

        let app = Gio.Application.get_default();
        this._category = category;
        this._mainWindow = app.mainWindow;
        this._model = app.appListModel;
        this._lastPageId = null;
        this._view = null;

        // Where the content goes once the frame is populated
        this._contentBox = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL,
                                         hexpand: true,
                                         vexpand: true });
        this._stack.add_named(this._contentBox, CONTENT_PAGE);

        let separator = new Separator.FrameSeparator();
        this._contentBox.add(separator);

        this._scrollWindow = new Gtk.ScrolledWindow({ hscrollbar_policy: Gtk.PolicyType.NEVER,
                                                      vscrollbar_policy: Gtk.PolicyType.AUTOMATIC });
        this._contentBox.add(this._scrollWindow);

        // The spinner displayed while the frame is being populated
        this._spinnerBox = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL,
                                         hexpand: true,
                                         vexpand: true });
        this._stack.add_named(this._spinnerBox, SPINNER_PAGE);
        this._spinnerBox.show();

        this._spinnerBox.add(new Separator.FrameSeparator());

        this._spinner = new Gtk.Spinner({ halign: Gtk.Align.CENTER,
                                          valign: Gtk.Align.CENTER,
                                          hexpand: true,
                                          vexpand: true });
        this._spinnerBox.add(this._spinner);
        this.spinning = true;

        this._backClickedId = 0;
        this.connect('destroy', Lang.bind(this, this._onDestroy));

        this.show_all();
    },

    _onDestroy: function() {
        if (this._backClickedId != 0) {
            this._mainWindow.disconnect(this._backClickedId);
            this._backClickedId = 0;
        }
    },

    _onPageChanged: function() {
        let pageId = this._stack.visible_child_name;
        if (pageId != SPINNER_PAGE) {
            this._lastPageId = pageId;
        }
    },

    set spinning(v) {
        if (v) {
            this._stack.set_visible_child_full(SPINNER_PAGE, Gtk.StackTransitionType.CROSSFADE);
            this._spinner.start();
        } else {
            let pageId = this._lastPageId || CONTENT_PAGE;
            this._stack.set_visible_child_full(pageId, Gtk.StackTransitionType.CROSSFADE);
            this._spinner.stop();
        }
    },

    get spinning() {
        return (this._stack.visible_child_name == SPINNER_PAGE);
    },

    get mainWindow() {
        return this._mainWindow;
    },

    get model() {
        return this._model;
    },

    get contentBox() {
        return this._contentBox;
    },

    get scrollWindow() {
        return this._scrollWindow;
    },

    get view() {
        return this._view;
    },

    set view(v) {
        if (v)
            this.scrollWindow.add(v);

        this._view = v;

        if (v)
            this.spinning = false;
    },

    _createView: function() {
        // to be overridden
    },

    _createViewElement: function() {
        // to be overridden
    },

    _destroyView: function() {
        let child = this.scrollWindow.get_child();
        if (child)
            child.destroy();
        this.view = null;
    },

    _prepareAppInfos: function(appInfos) {
        // to be overridden
    },

    _populateView: function(appInfos) {
        for (let info of appInfos) {
            this._createViewElement(info);
        }
    },

    _doPopulate: function() {
        this.view = this._createView();
        let appInfos = this._prepareAppInfos(this._model.loadCategory(this._category.id));
        this._populateView(appInfos);
    },

    populate: function() {
        if (this.view) {
            return;
        }

        if (this._model.loading) {
            return;
        }

        this._doPopulate();
    },

    _showView: function() {
        this._mainWindow.clearHeaderState();

        if (this._backClickedId != 0) {
            this._mainWindow.disconnect(this._backClickedId);
            this._backClickedId = 0;
        }

        this.populate();
        this._stack.set_visible_child_full(CONTENT_PAGE, Gtk.StackTransitionType.SLIDE_RIGHT);
    },

    getIcon: function() {
        return this._category.icon;
    },

    getName: function() {
        return this._category.label;
    },

    showAppInfoBox: function(appInfo) {
        let desktopId = appInfo.get_desktop_id();
        if (!this._stack.get_child_by_name(desktopId)) {
            let appBox = new AppInfoBox.AppInfoBox(appInfo);
            this._stack.add_named(appBox, desktopId);
            appBox.show();
        }

        this._stack.set_visible_child_full(desktopId, Gtk.StackTransitionType.SLIDE_LEFT);

        this._mainWindow.titleText = appInfo.get_title();
        this._mainWindow.subtitleText = appInfo.get_subtitle();
        this._mainWindow.headerIcon = appInfo.get_icon_name();
        this._mainWindow.headerInstalledVisible = appInfo.is_installed();
        this._mainWindow.backButtonVisible = true;

        this._backClickedId =
            this._mainWindow.connect('back-clicked', Lang.bind(this, this._showView));
    },

    invalidate: function() {
        this._destroyView();
        this._mainWindow.clearHeaderState();
    },

    reset: function() {
        if (this.spinning) {
            return;
        }

        this._showView();
    }
});

const AppInstalledFrame = new Lang.Class({
    Name: 'AppInstalledFrame',
    Extends: AppFrame,

    _onDestroy: function() {
        this._unschedulePopulate();
        this.parent();
    },

    _listHeaderFunc: function(row, before) {
        if (before) {
            let frame = new Gtk.Frame();
            frame.get_style_context().add_class('app-installed-list-separator');
            row.set_header(frame);
        }
    },

    _createView: function() {
        let list = new Gtk.ListBox({ expand: true,
                                     selection_mode: Gtk.SelectionMode.NONE,
                                     visible: true });
        list.get_style_context().add_class('app-installed-list');
        list.connect('row-activated', Lang.bind(this, this._onRowActivated));
        list.set_header_func(Lang.bind(this, this._listHeaderFunc));

        return list;
    },

    _destroyView: function() {
        this._unschedulePopulate();
        this.parent();
    },

    _createViewElement: function(info) {
        let row = new AppInstalledBox.AppInstalledBoxRow(info);
        this.view.add(row);
        row.show();
    },

    _unschedulePopulate: function() {
        if (this._populateId > 0) {
            GLib.source_remove(this._populateId);
            this._populateId = 0;
        }
    },

    _schedulePopulate: function(appInfos) {
        if (appInfos.length > 0) {
            this._populateId = GLib.idle_add(
                GLib.PRIORITY_DEFAULT_IDLE + 20,
                Lang.bind(this, this._populateMoreInfos, appInfos));
        }
    },

    _populateBatchSize: function() {
        // assume 12 rows at 1080 screen resolution and scale it from there
        let screenHeight = this.get_screen().get_height();
        return Math.floor(screenHeight / 1080 * 12);
    },

    _populateMoreInfos: function(appInfos) {
        this._populateId = 0;

        for (let idx = 0; idx < this._populateBatchSize() && appInfos.length > 0; idx++) {
            let info = appInfos.shift();
            this._createViewElement(info);
        }

        this._schedulePopulate(appInfos);

        return GLib.SOURCE_REMOVE;
    },

    _populateView: function(appInfos) {
        this._populateMoreInfos(appInfos);
    },

    _prepareAppInfos: function(appInfos) {
        return appInfos.filter(function(info) {
            return info.is_installed();
        }).sort(function(a, b) {
            let aUpdatable = a.is_updatable();
            let bUpdatable = b.is_updatable();

            // If both apps are updatable, or both aren't, sort them
            // alphabetically, otherwise sort updatable apps first.
            if (aUpdatable == bUpdatable) {
                return a.get_title().localeCompare(b.get_title());
            }

            if (aUpdatable) {
                return 1;
            }

            // bUpdatable will be true here
            return -1;
        });
    },

    _onRowActivated: function(list, row) {
        let installedBox = row.get_child();
        this.showAppInfoBox(installedBox.appInfo);
    },

    _doPopulate: function() {
        this._unschedulePopulate();
        this.parent();
    },

    getTitle: function() {
        return _("Installed apps");
    }
});

const AppCategoryFrame = new Lang.Class({
    Name: 'AppCategoryFrame',
    Extends: AppFrame,

    _init: function(category) {
        this.parent(category);

        this._lastCellSelected = null;
    },

    _createView: function() {
        let cellMargin = EosAppStorePrivate.AppInfo.get_cell_margin();
        let grid = new EosAppStorePrivate.FlexyGrid({ cell_size: CELL_DEFAULT_SIZE + cellMargin,
                                                      cell_spacing: CELL_DEFAULT_SPACING - cellMargin,
                                                      visible: true });
        grid.connect('cell-selected', Lang.bind(this, this._onCellSelected));
        grid.connect('cell-activated', Lang.bind(this, this._onCellActivated));

        return grid;
    },

    _createViewElement: function(info) {
        let cell = info.create_cell(info.get_icon_name());
        cell.show_all();
        this.view.add(cell);
    },

    _prepareAppInfos: function(appInfos) {
        // Every category only shows apps that can be added
        return appInfos.filter(function(info) {
            return !info.get_has_launcher();
        });
    },

    _onCellSelected: function(grid, cell) {
        if (this._lastCellSelected != cell) {
            if (this._lastCellSelected) {
                this._lastCellSelected.selected = false;
            }

            this._lastCellSelected = cell;

            if (this._lastCellSelected) {
                this._lastCellSelected.selected = true;
            }
        }
    },

    _onCellActivated: function(grid, cell) {
        this.showAppInfoBox(cell.app_info);
    },

    getTitle: function() {
        return _("Install apps");
    }
});

const AppPageProvider = new Lang.Class({
    Name: 'AppPageProvider',
    Implements: [AppStorePages.AppStorePageProvider],

    _init: function() {
        let app = Gio.Application.get_default();
        this._model = app.appListModel;
        this._pageManager = app.mainWindow.pageManager;
        this._categories = Categories.get_app_categories();

        this._model.connect('loading-changed', Lang.bind(this, this._onModelLoadingChanged));
        this._onModelLoadingChanged();
    },

    _onModelLoadingChanged: function(model) {
        if (this._model.loading) {
            return;
        }

        this._repopulateActivePage();
        this._model.refresh(Lang.bind(this, this._onModelRefresh));
    },

    _onModelChanged: function() {
        this._reloadModel();
    },

    _onModelRefresh: function(error) {
        if (error) {
            if (error.matches(EosAppStorePrivate.app_store_error_quark(),
                              EosAppStorePrivate.AppStoreError.APP_REFRESH_FAILURE)) {
                let app = Gio.Application.get_default();

                // Show the error dialog
                let dialog = new Gtk.MessageDialog({ transient_for: app._mainWindow,
                                                     modal: true,
                                                     destroy_with_parent: true,
                                                     text: _("Refresh failed"),
                                                     secondary_text: error.message });
                dialog.add_button(_("Dismiss"), Gtk.ResponseType.OK);
                dialog.show_all();
                dialog.run();
                dialog.destroy();

                // On critical failures we don't try to partially populate
                // categories
                return;
            } else {
                log("Loading apps anyways due to non-critical exceptions");
            }
        }

        // now start listening to changes
        this._model.connect('changed', Lang.bind(this, this._onModelChanged));
        this._reloadModel();
    },

    _reloadModel: function() {
        // invalidate all the pages
        this._categories.forEach(Lang.bind(this, function(c) {
            let page = this._pageManager.get_child_by_name(c.name);
            if (page) {
                page.invalidate();
            }
        }));

        this._repopulateActivePage();
    },

    _repopulateActivePage: function() {
        // repopulate current page if it belongs to us
        let activePageId = this._pageManager.visible_child_name;
        if (this._findCategory(activePageId)) {
            let activePage = this._pageManager.visible_child;
            activePage.invalidate();
            activePage.populate();
        }
    },

    _findCategory: function(pageId) {
        for (let category of this._categories) {
            if (category.name == pageId) {
                return category;
            }
        }

        return null;
    },

    createPage: function(pageId) {
        let category = this._findCategory(pageId);
        if (category.id == EosAppStorePrivate.AppCategory.INSTALLED) {
            return new AppInstalledFrame(category);
        }

        return new AppCategoryFrame(category);
    },

    getPageIds: function() {
        return this._categories.map(function(c) {
            return c.name;
        });
    }
});
