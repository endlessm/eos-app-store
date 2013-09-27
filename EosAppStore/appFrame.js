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
const Builder = imports.builder;
const Lang = imports.lang;
const Signals = imports.signals;

const APP_TRANSITION_MS = 500;
const CATEGORY_TRANSITION_MS = 500;

const CATEGORIES_BOX_SPACING = 32;
const STACK_TOP_MARGIN = 15;

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
        '_icon',
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
        this.appIcon = this._model.getIcon(this._appId);
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

    set appIcon(name) {
        if (!name) {
            name = "gtk-missing-image";
        }

        this._icon.set_from_icon_name(name, Gtk.IconSize.DIALOG);
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

const AppCategoryButton = new Lang.Class({
    Name: 'AppCategoryButton',
    Extends: Gtk.RadioButton,
    Properties: { 'category': GObject.ParamSpec.string('category',
                                                       'Category',
                                                       'The category name',
                                                       GObject.ParamFlags.READABLE |
                                                       GObject.ParamFlags.WRITABLE |
                                                       GObject.ParamFlags.CONSTRUCT,
                                                       '') },
    _init: function(params) {
        this._category = '';

        this.parent(params);

        this.get_style_context().add_class('app-category-button');
    },

    get category() {
        return this._category;
    },

    set category(c) {
        if (this._category == c) {
            return;
        }

        this._category = c;
        this.notify('category');
    }
});


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

        let separator = new Gtk.Separator({ orientation: Gtk.Orientation.HORIZONTAL });
        separator.get_style_context().add_class('frame-separator');
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
    },

    _populateCategories: function() {
        for (let c in this._categories) {
            let category = this._categories[c];

            if (!category.button) {
                category.button = new AppCategoryButton({ label: category.label,
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

            let grid = new Endless.FlexyGrid();
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
        app.mainWindowTitle = cell.app_info.get_title();
        app.mainWindowSubtitle = cell.app_info.get_subtitle();
    },

    _onCategoryClicked: function(button) {
        let category = button.category;
        this._stack.set_visible_child_name(category);
    },

    reset: function() {
        this._mainStack.set_visible_child_name('main-box');        
    }
});
