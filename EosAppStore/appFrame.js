// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const PLib = imports.gi.PLib;

const AppListModel = imports.appListModel;
const Builder = imports.builder;
const Lang = imports.lang;
const Signals = imports.signals;

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
        if (!name)
            name = _("Unknown application");

        this._appNameLabel.set_text(name);
    },

    set appDescription(description) {
        if (!description)
            description = "";

        this._appDescriptionLabel.set_text(description);
    },

    set appIcon(name) {
        if (!name)
            name = "gtk-missing-image";

        this._appIcon.set_from_icon_name(name, Gtk.IconSize.DIALOG);
    },

    set appState(state) {
        this._appState = state;
        this._appStateButton.hide();

        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._appStateButton.set_label('UNINSTALL');
                this._appStateButton.show();
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._appStateButton.set_label('INSTALL');
                this._appStateButton.show();
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                this._appStateButton.set_label('UPDATE');
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

    _init: function() {
        this.parent();
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

    templateResource: '/com/endlessm/appstore/eos-app-store-app-frame.ui',
    templateChildren: [
        '_mainBox',
        '_scrolledWindow',
        '_viewport',
    ],

    _init: function() {
        this.parent();

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });

        this._appListModel = new AppListModel.AppList();
        this._appListModel.connect('changed', Lang.bind(this, this._onListModelChange));

        this._stack = new PLib.Stack();
        this._stack.set_transition_duration(250);
        this._stack.set_transition_type(PLib.StackTransitionType.SLIDE_RIGHT);
        this.add(this._stack);
        this._stack.show();

        this._stack.add_named(this._mainBox, 'app-list');
        this._mainBox.hexpand = true;
        this._mainBox.vexpand = true;
        this._mainBox.show();

        this._listBox = new AppListBox();
        this._viewport.add(this._listBox);
        this._listBox.show_all();

        this._descriptionBox = new AppDescriptionBox();
        this._descriptionBox.hexpand = true;
        this._descriptionBox.vexpand = true;
        this._stack.add_named(this._descriptionBox, 'app-description');
        this._descriptionBox.show();

        this._stack.set_visible_child_name('app-list');
    },

    _onListModelChange: function(model, apps) {
        this._listBox.foreach(function(child) { child.destroy(); });

        apps.forEach(Lang.bind(this, function(item) {
            if (!model.getAppVisible(item))
              return;

            let row = new AppListBoxRow(this._appListModel, item);

            row.appName = model.getAppName(item);
            row.appDescription = model.getAppDescription(item);
            row.appIcon = model.getAppIcon(item);
            row.appState = model.getAppState(item);

            this._listBox.add(row);
            row.show();
        }));
    },

    update: function() {
        this._appListModel.update();
    },
});
Builder.bindTemplateChildren(AppFrame.prototype);
