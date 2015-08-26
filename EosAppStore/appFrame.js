// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Mainloop = imports.mainloop;

const AppInfoBox = imports.appInfoBox;
const AppListModel = imports.appListModel;
const AppStoreWindow = imports.appStoreWindow;
const Builder = imports.builder;
const Categories = imports.categories;
const CategoryButton = imports.categoryButton;
const Lang = imports.lang;
const Notify = imports.notify;
const Separator = imports.separator;
const Signals = imports.signals;

const APP_TRANSITION_MS = 500;

const CELL_DEFAULT_SIZE = 180;
const CELL_DEFAULT_SPACING = 15;

const AppCategoryFrame = new Lang.Class({
    Name: 'AppCategoryFrame',
    Extends: Gtk.Frame,

    _init: function(category, model, mainWindow) {
        this.parent();

        this.get_style_context().add_class('app-frame');

        this._stack = new Gtk.Stack({ transition_duration: APP_TRANSITION_MS,
                                      transition_type: Gtk.StackTransitionType.SLIDE_RIGHT,
                                      hexpand: true,
                                      vexpand: true });
        this.add(this._stack);

        this._category = category;
        this._mainWindow = mainWindow;
        this._model = model;

        this._backClickedId = 0;
        this._lastCellSelected = null;
        this._gridBox = null;

        this._spinnerBox = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL,
                                         hexpand: true,
                                         vexpand: true });
        this._stack.add_named(this._spinnerBox, 'spinner');
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
            this._stack.set_visible_child_full('spinner', Gtk.StackTransitionType.CROSSFADE);
            this._spinner.start();
        } else {
            this._stack.set_visible_child_full('app-frame', Gtk.StackTransitionType.CROSSFADE);
            this._spinner.stop();
        }
    },

    get spinning() {
        return (this._stack.visible_child_name == 'spinner');
    },

    populate: function() {
        if (this._gridBox) {
            return;
        }

        this._gridBox = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL,
                                      hexpand: true,
                                      vexpand: true });
        this._stack.add_named(this._gridBox, 'app-frame');

        let separator = new Separator.FrameSeparator();
        this._gridBox.add(separator);

        let scrollWindow = new Gtk.ScrolledWindow({ hscrollbar_policy: Gtk.PolicyType.NEVER,
                                                    vscrollbar_policy: Gtk.PolicyType.AUTOMATIC });
        this._gridBox.add(scrollWindow);

        let cellMargin = EosAppStorePrivate.AppInfo.get_cell_margin();
        let grid = new EosAppStorePrivate.FlexyGrid({ cell_size: CELL_DEFAULT_SIZE + cellMargin,
                                                      cell_spacing: CELL_DEFAULT_SPACING - cellMargin });
        scrollWindow.add_with_viewport(grid);

        let appInfos = this._model.loadCategory(this._category.id);

        if (this._category.id == EosAppStorePrivate.AppCategory.INSTALLED) {
            let sortedAppInfos = appInfos.sort(function(a, b) {
                return b.get_installation_time() - a.get_installation_time();
            });

            // 'Installed' only shows apps available on the desktop...
            for (let i in sortedAppInfos) {
                let info = sortedAppInfos[i];

                if (info.get_has_launcher()) {
                    let cell = info.create_cell(info.get_icon_name());
                    cell.shape = EosAppStorePrivate.FlexyShape.SMALL;
                    grid.add(cell);
                }
            }
        }
        else {
            // ... while every other category only shows apps that can be added
            for (let i in appInfos) {
                let info = appInfos[i];

                if (!info.get_has_launcher()) {
                    let cell = info.create_cell(info.get_icon_name());
                    grid.add(cell);
                }
            }
        }

        grid.connect('cell-selected', Lang.bind(this, this._onCellSelected));
        grid.connect('cell-activated', Lang.bind(this, this._onCellActivated));

        this._gridBox.show_all();
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
            let appBox = new AppInfoBox(this._model, cell.app_info);
            appBox.show();

            appBox.connect('destroy', Lang.bind(this, this._showGrid));

            this._stack.add_named(appBox, cell.desktop_id);
        }

        this._stack.set_visible_child_full(cell.desktop_id, Gtk.StackTransitionType.SLIDE_LEFT);

        this._mainWindow.titleText = cell.app_info.get_title();
        this._mainWindow.subtitleText = cell.app_info.get_subtitle();
        this._mainWindow.headerIcon = cell.app_info.get_icon_name();
        this._mainWindow.headerInstalledVisible = cell.app_info.is_installed();
        this._mainWindow.backButtonVisible = true;

        this._backClickedId =
            this._mainWindow.connect('back-clicked', Lang.bind(this, this._showGrid));
    },

    _showGrid: function() {
        this._mainWindow.clearHeaderState();

        if (this._backClickedId > 0) {
            this._mainWindow.disconnect(this._backClickedId);
            this._backClickedId = 0;
        }

        this.populate();
        this._stack.transition_type = Gtk.StackTransitionType.SLIDE_RIGHT;
        this._stack.set_visible_child(this._gridBox);
    },

    reset: function() {
        if (this.spinning) {
            return;
        }

        this._gridBox.destroy();
        this._gridBox = null;
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
            category.widget = new AppCategoryFrame(category, this._model, mainWindow);
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
