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

        this._backClickedId = 0;
        this._stack = new Gtk.Stack({ transition_duration: APP_TRANSITION_MS,
                                      transition_type: Gtk.StackTransitionType.SLIDE_RIGHT,
                                      hexpand: true,
                                      vexpand: true,
                                      homogeneous: false });
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

        this._scrollWindow = new Gtk.ScrolledWindow({ shadow_type: Gtk.ShadowType.IN,
                                                      hscrollbar_policy: Gtk.PolicyType.NEVER,
                                                      vscrollbar_policy: Gtk.PolicyType.AUTOMATIC,
                                                      margin_bottom: 15 });
        this._scrollWindow.get_style_context().add_class('app-scrolledwindow');
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

        this.connect('destroy', Lang.bind(this, this._onDestroy));

        this.show_all();
    },

    _onDestroy: function() {
        this._clearBackId();
    },

    _setupPageHeader: function() {
        let appInfo = this._stack.visible_child.appInfo;
        if (!appInfo) {
            return;
        }

        this._mainWindow.titleText = appInfo.get_title();
        this._mainWindow.subtitleText = appInfo.get_subtitle();
        this._mainWindow.headerIcon = appInfo.get_icon_name();
        this._mainWindow.headerInstalledVisible = appInfo.is_installed();
        this._mainWindow.backButtonVisible = true;

        this._clearBackId();
        this._backClickedId =
            this._mainWindow.connect('back-clicked', Lang.bind(this, this._showView));
    },

    _clearBackId: function() {
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

        if (pageId == SPINNER_PAGE ||
            pageId == CONTENT_PAGE) {
            this._mainWindow.clearHeaderState();
            this._clearBackId();
        } else {
            this._setupPageHeader();
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

    get view() {
        return this._view;
    },

    set view(v) {
        if (v)
            this._scrollWindow.add(v);

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
        let child = this._scrollWindow.get_child();
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
    },

    invalidate: function() {
        this._destroyView();
    },

    reset: function() {
        if (this.spinning) {
            return;
        }

        this._showView();
    },

    get canSearch() {
        // We cannot search while we're populating the model
        return !this.spinning;
    }
});

const AppInstalledFrame = new Lang.Class({
    Name: 'AppInstalledFrame',
    Extends: AppFrame,

    _init: function(params) {
        this.parent(params);
        this.get_style_context().add_class('app-installed-frame');
    },

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
            // The sorting is thus defined:
            //
            // - updatable apps, sorted alphabetically, always go first
            // - system apps, sorted alphabetically, always go last
            // - everything else, it's in the middle
            let aUpdatable = a.is_updatable();
            let bUpdatable = b.is_updatable();
            let aSystemApp = !a.is_store_installed();
            let bSystemApp = !b.is_store_installed();

            // If both apps are updatable, or both aren't, sort them
            // alphabetically, otherwise sort updatable apps first. If
            // both aren't updatable, but either is a system app, then
            // we sort the last.
            if (aUpdatable == bUpdatable) {
                if (aSystemApp && bSystemApp) {
                    return a.get_title().localeCompare(b.get_title());
                }

                // System apps go to the bottom
                if (aSystemApp) {
                    return 1;
                }

                if (bSystemApp) {
                    return -1;
                }

                // Otherwise, sort alphabetically
                return a.get_title().localeCompare(b.get_title());
            }

            // System apps are never updatable, and updatable apps go to the top
            if (aUpdatable) {
                return -1;
            }

            if (bUpdatable) {
                return 1;
            }

            // System apps go to the bottom
            return aSystemApp ? 1 : -1;
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

    _showView: function() {
        if (this._invalidated) {
            this._destroyView();
            this._invalidated = false;
        }

        this.parent();
    },

    invalidate: function() {
        // Instead of destroying the view, we queue an invalidation
        // on next page reset, as we don't want to resort while showing
        this._invalidated = true;
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

    _destroyView: function() {
        this._lastCellSelected = null;
        this.parent();
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

const AppSearchFrame = new Lang.Class({
    Name: 'AppSearchFrame',
    Extends: AppCategoryFrame,

    _init: function(category) {
        this.parent(category);

        this._mainWindow.search_entry.connect('search-changed', Lang.bind(this, this._onSearchChanged));
        this._searchTerms = null;
    },

    _onPageChanged: function() {
        this.parent();

        if (this._lastPageId != CONTENT_PAGE) {
            // save search terms to go back to later
            this._searchTerms = this._mainWindow.searchTerms;
            this._mainWindow.clearSearchState();
        }
        else if (this._searchTerms) {
            // resume search
            this._mainWindow.searchTerms = this._searchTerms;
            this._searchTerms = null;
        }
    },

    _onSearchChanged: function() {
        this._model.searchTerms(this._mainWindow.searchTerms);
    },

    _prepareAppInfos: function(appInfos) {
        // No filtering applied to searches
        return appInfos;
    },

    getTitle: function() {
        return _("Search results");
    },

    getName: function() {
        return null;
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
                app.maybeNotifyUser(_("Refresh failed"), error);

                // On critical failures we don't try to partially populate
                // categories
                return;
            }

            log("Loading apps anyways due to non-critical exceptions");
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

        if (category.id == EosAppStorePrivate.AppCategory.SEARCH) {
            return new AppSearchFrame(category);
        }

        return new AppCategoryFrame(category);
    },

    getPageIds: function() {
        return this._categories.map(function(c) {
            return c.name;
        });
    }
});
