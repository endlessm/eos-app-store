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

const CATEGORY_TRANSITION_MS = 500;

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
        '_appIcon',
        '_appNameLabel',
        '_appDescriptionLabel',
        '_appStateButton',
    ],

    _init: function(model, appId) {
        this.parent();

        this._model = model;
        this._appId = appId;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);
        this._mainBox.show();

        this._appStateButton.connect('clicked', Lang.bind(this, this._onAppStateButtonClicked));
    },

    get appId() {
        return this._appId;
    },

    set appName(name) {
        if (!name) {
            name = _("Unknown application");
        }

        this._appNameLabel.set_text(name);
    },

    set appDescription(description) {
        if (!description) {
            description = "";
        }

        this._appDescriptionLabel.set_text(description);
    },

    set appIcon(name) {
        if (!name) {
            name = "gtk-missing-image";
        }

        this._appIcon.set_from_icon_name(name, Gtk.IconSize.DIALOG);
    },

    set appState(state) {
        this._appState = state;
        this._appStateButton.hide();

        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._appStateButton.set_label(_("UNINSTALL"));
                this._appStateButton.show();
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._appStateButton.set_label(_("INSTALL"));
                this._appStateButton.show();
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                this._appStateButton.set_label(_("UPDATE"));
                this._appStateButton.show();
                break;

            default:
                break;
        }
    },

    _onAppStateButtonClicked: function() {
        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._model.uninstallApp(this._appId);
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._model.installApp(this._appId);
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                this._model.updateApp(this._appId);
                break;
        }
    },
});
Builder.bindTemplateChildren(AppListBoxRow.prototype);

const AppListBox = new Lang.Class({
    Name: 'AppListBox',
    Extends: PLib.ListBox,

    _init: function(model) {
        this.parent();

        this._model = model;
    },
});

const AppDescriptionBox = new Lang.Class({
    Name: 'AppDescriptionBox',
    Extends: Gtk.Frame,

    _init: function() {
        this.parent();
    },
});

const AppFrame = new Lang.Class({
    Name: 'AppFrame',
    Extends: Gtk.Frame,

    _init: function() {
        this.parent();

        this._mainBox = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL, });
        this.add(this._mainBox);
        this._mainBox.hexpand = true;
        this._mainBox.vexpand = true;
        this._mainBox.show();

        this._categoriesBox = new Gtk.Box({ orientation: Gtk.Orientation.HORIZONTAL, });
        this._categoriesBox.hexpand = true;
        this._mainBox.add(this._categoriesBox);
        this._categoriesBox.show();

        this._stack = new PLib.Stack();
        this._stack.set_transition_duration(CATEGORY_TRANSITION_MS);
        this._stack.set_transition_type(PLib.StackTransitionType.SLIDE_RIGHT);
        this._stack.hexpand = true;
        this._stack.vexpand = true;
        this._mainBox.add(this._stack);
        this._stack.show();

        this._populateCategories();
    },

    _populateCategories: function() {
        let categories = [
            {
                name: 'featured',
                button: null,
                grid: null,
                label: _("Featured"),
                id: EosAppStorePrivate.AppCategory.FEATURED,
            },
            {
                name: 'education',
                button: null,
                grid: null,
                label: _("Education"),
                id: EosAppStorePrivate.AppCategory.EDUCATION,
            },
            {
                name: 'leisure',
                button: null,
                grid: null,
                label: _("Leisure"),
                id: EosAppStorePrivate.AppCategory.LEISURE,
            },
            {
                name: 'utilities',
                button: null,
                grid: null,
                label: _("Utilities"),
                id: EosAppStorePrivate.AppCategory.UTILITIES,
            },
        ];

        this._categories = categories;

        for (let c in categories) {
            categories[c].button = new Gtk.Button({ label: categories[c].label, });
            categories[c].button.connect('clicked', Lang.bind(this, this._onCategoryClicked));
            categories[c].button.show();
            this._categoriesBox.add(categories[c].button);

            let scrollWindow = new Gtk.ScrolledWindow();
            this._stack.add_named(scrollWindow, categories[c].name);

            categories[c].grid = new Endless.FlexyGrid();
            categories[c].grid.set_size_request(MIN_GRID_WIDTH, MIN_GRID_HEIGHT);
            scrollWindow.add_with_viewport(categories[c].grid);

            let cells = EosAppStorePrivate.app_load_content(categories[c].grid, categories[c].id);
            for (let cell in cells) {
                categories[c].grid.add(cell);
            }

            scrollWindow.show_all();
        }
    },

    _onCategoryClicked: function(button) {
        let category = null;

        for (let c in this._categories) {
            if (this._categories[c].button == button) {
                category = this._categories[c];
                break;
            }
        }

        if (!category) {
            return;
        }

        this._stack.set_visible_child_name(category.name);
    },

    update: function() {
    },
});
