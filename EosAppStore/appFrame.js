// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const PLib = imports.gi.PLib;
const Endless = imports.gi.Endless;

const AppListModel = imports.appListModel;
const CategoryButton = imports.categoryButton;
const Builder = imports.builder;
const Lang = imports.lang;
const Separator = imports.separator;
const Signals = imports.signals;

const APP_TRANSITION_MS = 500;
const CATEGORY_TRANSITION_MS = 500;

const CELL_DEFAULT_SIZE = 180;
const CATEGORIES_BOX_SPACING = 32;
const STACK_TOP_MARGIN = 4;

// If the area available for the grid is less than this minimium size,
// scroll bars will be added.
const MIN_GRID_WIDTH = 800;
const MIN_GRID_HEIGHT = 600;

const AppListBoxRow = new Lang.Class({
    Name: 'AppListBoxRow',
    Extends: Gtk.Bin,

    templateResource: '/com/endlessm/appstore/eos-app-store-list-row.ui',
    templateChildren: [
        '_mainBox',
        '_descriptionLabel',
        '_stateButton',
    ],

    _init: function(model, appInfo) {
        this.parent();

        this._model = model;
        this._appId = appInfo.get_desktop_id();

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);
        this._mainBox.show();

        this._stateButton.connect('clicked', Lang.bind(this, this._onStateButtonClicked));

        this.appInfo = appInfo;
        this.appState = this._model.getState(this._appId);
        this.appDescription = this.appInfo.get_description();
    },

    get appId() {
        return this._appId;
    },

    set appDescription(description) {
        if (!description) {
            description = "";
        }

        this._descriptionLabel.set_text(description);
    },

    set appState(state) {
        this._appState = state;
        this._stateButton.hide();

        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._stateButton.set_label(_("UNINSTALL"));
                this._stateButton.show();
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._stateButton.set_label(_("INSTALL"));
                this._stateButton.show();
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                this._stateButton.set_label(_("UPDATE"));
                this._stateButton.show();
                break;

            default:
                break;
        }
    },

    _onStateButtonClicked: function() {
        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._model.uninstall(this._appId);
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._model.install(this._appId);
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                this._model.updateApp(this._appId);
                break;
        }
    },
});
Builder.bindTemplateChildren(AppListBoxRow.prototype);

const AppFrame = new Lang.Class({
    Name: 'AppFrame',
    Extends: Gtk.Frame,

    _init: function() {
        this.parent();

        this.get_style_context().add_class('app-frame');

        this._categories = [
            {
                name: 'featured',
                widget: null,
                label: _("Featured"),
                id: EosAppStorePrivate.AppCategory.FEATURED,
            },
            {
                name: 'education',
                widget: null,
                label: _("Education"),
                id: EosAppStorePrivate.AppCategory.EDUCATION,
            },
            {
                name: 'leisure',
                widget: null,
                label: _("Leisure"),
                id: EosAppStorePrivate.AppCategory.LEISURE,
            },
            {
                name: 'utilities',
                widget: null,
                label: _("Utilities"),
                id: EosAppStorePrivate.AppCategory.UTILITIES,
            },
        ];

        this._currentCategory = this._categories[0].name;

        // initialize the applications model
        this._model = new AppListModel.AppList();

        this._mainStack = new PLib.Stack();
        this._mainStack.set_transition_duration(APP_TRANSITION_MS);
        this._mainStack.set_transition_type(PLib.StackTransitionType.SLIDE_RIGHT);
        this._mainStack.hexpand = true;
        this._mainStack.vexpand = true;
        this.add(this._mainStack);
        this._mainStack.show();

        this._mainBox = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL, });
        this._mainStack.add_named(this._mainBox, 'main-box');
        this._mainBox.hexpand = true;
        this._mainBox.vexpand = true;
        this._mainBox.show();

        this._categoriesBox = new Gtk.Box({ orientation: Gtk.Orientation.HORIZONTAL,
                                            spacing: CATEGORIES_BOX_SPACING });
        this._categoriesBox.hexpand = true;
        this._mainBox.add(this._categoriesBox);
        this._categoriesBox.show();

        let separator = new Separator.FrameSeparator();
        this._mainBox.add(separator);

        this._stack = new PLib.Stack();
        this._stack.set_transition_duration(CATEGORY_TRANSITION_MS);
        this._stack.set_transition_type(PLib.StackTransitionType.SLIDE_RIGHT);
        this._stack.hexpand = true;
        this._stack.vexpand = true;
        this._stack.margin_top = STACK_TOP_MARGIN;
        this._mainBox.add(this._stack);
        this._stack.show();

        this._buttonGroup = null;
        this._model.connect('changed', Lang.bind(this, this._populateCategories));
        this._populateCategories();

        let content_dir = EosAppStorePrivate.app_get_content_dir();
        let content_path = GLib.build_filenamev([content_dir, 'content.json']);
        let content_file = Gio.File.new_for_path(content_path);
        this._contentMonitor = content_file.monitor_file(Gio.FileMonitorFlags.NONE, null);
        this._contentMonitor.connect('changed', Lang.bind(this, this._onContentChanged));

        this._stack.set_visible_child_name(this._currentCategory);
    },

    _onContentChanged: function(monitor, file, other_file, event_type) {
        this._populateCategories();
        this._stack.set_visible_child_name(this._currentCategory);
    },

    _populateCategories: function() {
        let cellStyle = EosAppStorePrivate.AppInfo.get_cell_style_context();
        let margin = cellStyle.get_margin(Gtk.StateFlags.NORMAL);
        let cellMargin = Math.max(margin.top, margin.right, margin.bottom, margin.left);

        for (let c in this._categories) {
            let category = this._categories[c];

            if (!category.button) {
                category.button = new CategoryButton.CategoryButton({ label: category.label,
                                                                      category: category.name,
                                                                      draw_indicator: false,
                                                                      group: this._buttonGroup });
                category.button.connect('clicked', Lang.bind(this, this._onCategoryClicked));
                category.button.show();
                this._categoriesBox.pack_start(category.button, false, false, 0);

                if (!this._buttonGroup) {
                    this._buttonGroup = category.button;
                }
            }

            let scrollWindow;

            if (!category.widget) {
                scrollWindow = new Gtk.ScrolledWindow({ hscrollbar_policy: Gtk.PolicyType.NEVER,
                                                        vscrollbar_policy: Gtk.PolicyType.AUTOMATIC });
                this._stack.add_named(scrollWindow, category.name);
                category.widget = scrollWindow;
            } else {
                scrollWindow = category.widget;
                let child = scrollWindow.get_child();
                child.destroy();
            }

            let grid = new Endless.FlexyGrid({ cell_size: CELL_DEFAULT_SIZE + cellMargin });
            scrollWindow.add_with_viewport(grid);

            let cells = EosAppStorePrivate.app_load_content(grid, category.id);
            for (let cell in cells) {
                grid.add(cell);
            }

            grid.connect('cell-activated', Lang.bind(this, this._onCellActivated));

            scrollWindow.show_all();
        }
    },

    _onCellActivated: function(grid, cell) {
        let appBox = new AppListBoxRow(this._model, cell.app_info);
        appBox.show_all();

        this._mainStack.add_named(appBox, cell.desktop_id);
        this._mainStack.set_visible_child_name(cell.desktop_id);

        let app = Gio.Application.get_default();
        app.mainWindow.titleText = cell.app_info.get_title();
        app.mainWindow.subtitleText = cell.app_info.get_subtitle();
        app.mainWindow.headerIcon = this._model.getIcon(cell.desktop_id);
        app.mainWindow.backButtonVisible = true;
        this._backClickedId =
            app.mainWindow.connect('back-clicked', Lang.bind(this, this._onBackClicked));
    },

    _onBackClicked: function() {
        let app = Gio.Application.get_default();
        app.mainWindow.titleText = null;
        app.mainWindow.subtitleText = null;
        app.mainWindow.headerIcon = null;
        app.mainWindow.backButtonVisible = false;
        app.mainWindow.disconnect(this._backClickedId);
        this._backClickedId = 0;

        let page = this._mainStack.get_visible_child();
        this._mainStack.set_visible_child_name('main-box');
        page.destroy();
    },

    _onCategoryClicked: function(button) {
        let category = button.category;

        this._currentCategory = category;
        this._stack.set_visible_child_name(category);
    }
});
