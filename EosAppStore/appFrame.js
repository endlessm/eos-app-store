// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;
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

    _init: function() {
        this.parent();

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);
        this._mainBox.show();
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
        if (state == 'installed') {
            this._appStateButton.set_label('INSTALLED');
            this._appStateButton.show();
            return;
        }

        this._appStateButton.hide();
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
        this.add(this._mainBox);
        this._mainBox.hexpand = true;
        this._mainBox.vexpand = true;
        this._mainBox.show();

        this._listBox = new AppListBox();
        this._viewport.add(this._listBox);
        this._listBox.show_all();

        this._appListModel = new AppListModel.AppList();
        this._appListModel.connect('changed', Lang.bind(this, this._onListModelChange));
    },

    _onListModelChange: function(model, apps) {
        this._listBox.foreach(function(child) { child.destroy(); });

        apps.forEach(Lang.bind(this, function(item) {
            let row = new AppListBoxRow();

            row.appName = model.getAppName(item);
            row.appDescription = model.getAppDescription(item);
            row.appIcon = model.getAppIcon(item);
            row.appState = 'installed'

            this._listBox.add(row);
            row.show();
        }));
    },

    update: function() {
        this._appListModel.update();
    },
});
Builder.bindTemplateChildren(AppFrame.prototype);
