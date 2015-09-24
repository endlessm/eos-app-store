// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;

const AppInfoBox = imports.appInfoBox;
const AppInstalledBox = imports.appInstalledBox;
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

    _init: function(model, mainWindow, categoryId) {
        this.parent();

        this.get_style_context().add_class('app-frame');

        this._stack = new Gtk.Stack({ transition_duration: APP_TRANSITION_MS,
                                      transition_type: Gtk.StackTransitionType.SLIDE_RIGHT,
                                      hexpand: true,
                                      vexpand: true });
        this.add(this._stack);

        this._categoryId = categoryId;
        this._mainWindow = mainWindow;
        this._model = model;
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

    set spinning(v) {
        if (v) {
            this._stack.set_visible_child_full(SPINNER_PAGE, Gtk.StackTransitionType.CROSSFADE);
            this._spinner.start();
        } else {
            this._stack.set_visible_child_full(CONTENT_PAGE, Gtk.StackTransitionType.CROSSFADE);
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

    get categoryId() {
        return this._categoryId;
    },

    _createView: function() {
        // to be overridden
    },

    _prepareAppInfos: function(appInfos) {
        // to be overridden
    },

    populate: function() {
        if (this.view) {
            return;
        }

        this.view = this._createView();
        let appInfos = this._prepareAppInfos(this.model.loadCategory(this._categoryId));

        // 'Installed' only shows apps available on the system
        for (let i in appInfos) {
            this._createViewElement(appInfos[i]);
        }
    },

    _showView: function() {
        this.mainWindow.clearHeaderState();

        if (this._backClickedId != 0) {
            this.mainWindow.disconnect(this._backClickedId);
            this._backClickedId = 0;
        }

        this.populate();
        this._stack.set_visible_child_full(CONTENT_PAGE, Gtk.StackTransitionType.SLIDE_RIGHT);
    },

    showAppInfoBox: function(appInfo) {
        let desktopId = appInfo.get_desktop_id();
        if (!this._stack.get_child_by_name(desktopId)) {
            let appBox = new AppInfoBox.AppInfoBox(this._model, appInfo);
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

    reset: function() {
        if (this.spinning) {
            return;
        }

        this.scrollWindow.get_child().destroy();
        this.view = null;

        this._showView();
    }
});

const AppInstalledFrame = new Lang.Class({
    Name: 'AppInstalledFrame',
    Extends: AppFrame,

    _init: function(model, mainWindow) {
        this.parent(model, mainWindow, EosAppStorePrivate.AppCategory.INSTALLED);
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

    _createViewElement: function(info) {
        let row = new AppInstalledBox.AppInstalledBox(this.model, info);
        this.view.add(row);
        row.show();
    },

    _prepareAppInfos: function(appInfos) {
        return appInfos.filter(function(info) {
            return info.is_installed();
        }).sort(function(a, b) {
            return b.get_installation_time() - a.get_installation_time();
        });
    },

    _onRowActivated: function(list, row) {
        let installedBox = row.get_child();
        this.showAppInfoBox(installedBox.appInfo);
    },

    get title() {
        return _("Installed apps");
    }
});

const AppCategoryFrame = new Lang.Class({
    Name: 'AppCategoryFrame',
    Extends: AppFrame,

    _init: function(categoryId, model, mainWindow) {
        this.parent(model, mainWindow, categoryId);

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

    get title() {
        return _("Install apps");
    }
});

const AppBroker = new Lang.Class({
    Name: 'AppBroker',

    _init: function(mainWindow) {
        this._mainWindow = mainWindow;

        // initialize the applications model
        let application = Gio.Application.get_default();
        this._model = application.appList;
        this._model.refresh(Lang.bind(this, this._onModelRefresh));

        this._categories = Categories.get_app_categories();
        this._categories.forEach(Lang.bind(this, function(category) {
            if (category.id == EosAppStorePrivate.AppCategory.INSTALLED) {
                category.widget = new AppInstalledFrame(this._model, mainWindow);
            } else {
                category.widget = new AppCategoryFrame(category.id, this._model, mainWindow);
            }
            category.widget.spinning = true;
        }));
    },

    _onModelRefresh: function(error) {
        if (error) {
            if (error.matches(EosAppStorePrivate.app_store_error_quark(),
                              EosAppStorePrivate.AppStoreError.APP_REFRESH_FAILURE)) {
                // Show the error dialog
                let dialog = new Gtk.MessageDialog({ transient_for: this._mainWindow,
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

        this._populateAllCategories();
    },

    _populateAllCategories: function() {
        this._categories.forEach(Lang.bind(this, function(c) {
            c.widget.populate();
        }));
    },

    get categories() {
        return this._categories;
    }
});
