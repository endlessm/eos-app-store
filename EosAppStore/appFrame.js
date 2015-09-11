// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Mainloop = imports.mainloop;

const AppInfoBox = imports.appInfoBox;
const AppInstalledBox = imports.appInstalledBox;
const AppListModel = imports.appListModel;
const AppStoreWindow = imports.appStoreWindow;
const Builder = imports.builder;
const Categories = imports.categories;
const CategoryButton = imports.categoryButton;
const Lang = imports.lang;
const Separator = imports.separator;
const Signals = imports.signals;

const APP_TRANSITION_MS = 500;

const CELL_DEFAULT_SIZE = 180;
const CELL_DEFAULT_SPACING = 15;

const CONTENT_PAGE = 'content';
const SPINNER_PAGE = 'spinner';

const AppFrame = new Lang.Class({
    Name: 'AppFrame',
    Extends: Gtk.Frame,

    _init: function(model, mainWindow) {
        this.parent();

        this.get_style_context().add_class('app-frame');

        this._stack = new Gtk.Stack({ transition_duration: APP_TRANSITION_MS,
                                      transition_type: Gtk.StackTransitionType.SLIDE_RIGHT,
                                      hexpand: true,
                                      vexpand: true });
        this.add(this._stack);

        this._mainWindow = mainWindow;
        this._model = model;

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

        this.show_all();
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

    populate: function() {
        // Base class is empty
    },

    addContentPage: function(pageId, pageWidget) {
        this._stack.add_named(pageWidget, pageId);
    },

    showContentPage: function(pageId, transition) {
        this._stack.set_visible_child_full(pageId, transition);
    },
});

const AppInstalledFrame = new Lang.Class({
    Name: 'AppInstalledFrame',
    Extends: AppFrame,

    _init: function(model, mainWindow) {
        this.parent(model, mainWindow);

        this._list = null;
    },

    populate: function() {
        if (this._list) {
            return;
        }

        let list = new Gtk.ListBox({ expand: true,
                                     selection_mode: Gtk.SelectionMode.NONE });
        list.get_style_context().add_class('app-installed-list');
        this.scrollWindow.add(list);

        let appInfos = this.model.loadCategory(EosAppStorePrivate.AppCategory.INSTALLED);
        let sortedAppInfos = appInfos.sort(function(a, b) {
            return b.get_installation_time() - a.get_installation_time();
        });

        // 'Installed' only shows apps available on the system
        for (let i in sortedAppInfos) {
            let info = sortedAppInfos[i];
            if (info.is_installed()) {
                let row = new AppInstalledBox.AppInstalledBox(this.model, info);
                list.add(row);
                row.show();
            }
        }

        list.show();

        // Keep a back reference so we can decide when to re-populate
        this._list = list;

        this.spinning = false;
    },

    reset: function() {
        if (this.spinning) {
            return;
        }

        this.scrollWindow.get_child().destroy();
        this._list = null;

        this.populate();
        this.showContentPage(CONTENT_PAGE, Gtk.StackTransitionType.SLIDE_RIGHT);
    },

    get title() {
        return _("Installed apps");
    }
});

const AppCategoryFrame = new Lang.Class({
    Name: 'AppCategoryFrame',
    Extends: AppFrame,

    _init: function(categoryId, model, mainWindow) {
        this.parent(model, mainWindow);

        this._categoryId = categoryId;

        this._grid = null;
        this._lastCellSelected = null;
        this._backClickedId = 0;
    },

    vfunc_destroy: function() {
        if (this._backClickedId != 0) {
            this.mainWindow.disconnect(this._backClickedId);
            this._backClickedId = 0;
        }

        this.parent();
    },

    populate: function() {
        if (this._grid) {
            return;
        }

        let cellMargin = EosAppStorePrivate.AppInfo.get_cell_margin();
        let grid = new EosAppStorePrivate.FlexyGrid({ cell_size: CELL_DEFAULT_SIZE + cellMargin,
                                                      cell_spacing: CELL_DEFAULT_SPACING - cellMargin });
        this.scrollWindow.add(grid);

        let appInfos = this.model.loadCategory(this._categoryId);

        // Every category only shows apps that can be added
        for (let i in appInfos) {
            let info = appInfos[i];

            if (!info.get_has_launcher()) {
                let cell = info.create_cell(info.get_icon_name());
                grid.add(cell);
            }
        }

        grid.connect('cell-selected', Lang.bind(this, this._onCellSelected));
        grid.connect('cell-activated', Lang.bind(this, this._onCellActivated));
        grid.show_all();

        // Keep a back reference so we can decide when to re-populate
        this._grid = grid;

        this.spinning = false;
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
        if (!this._stack.get_child_by_name(cell.desktop_id)) {
            let appBox = new AppInfoBox.AppInfoBox(this.model, cell.app_info);
            this.addContentPage(cell.desktop_id, appBox);
            appBox.connect('destroy', Lang.bind(this, this._showGrid));
            appBox.show();
        }

        this.showContentPage(cell.desktop_id, Gtk.StackTransitionType.SLIDE_LEFT);

        this.mainWindow.titleText = cell.app_info.get_title();
        this.mainWindow.subtitleText = cell.app_info.get_subtitle();
        this.mainWindow.headerIcon = cell.app_info.get_icon_name();
        this.mainWindow.headerInstalledVisible = cell.app_info.is_installed();
        this.mainWindow.backButtonVisible = true;

        this._backClickedId =
            this.mainWindow.connect('back-clicked', Lang.bind(this, this._showGrid));
    },

    _showGrid: function() {
        this.mainWindow.clearHeaderState();

        if (this._backClickedId != 0) {
            this.mainWindow.disconnect(this._backClickedId);
            this._backClickedId = 0;
        }

        this.populate();
        this.showContentPage(CONTENT_PAGE, Gtk.StackTransitionType.SLIDE_RIGHT);
    },

    reset: function() {
        if (this.spinning) {
            return;
        }

        this.scrollWindow.get_child().destroy();
        this._grid = null;
        this._showGrid();
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
