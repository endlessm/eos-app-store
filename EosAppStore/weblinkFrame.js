//: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const PLib = imports.gi.PLib;

const WeblinkListModel = imports.appListModel;
const Builder = imports.builder;
const Lang = imports.lang;
const Signals = imports.signals;

const WeblinkListBoxRow = new Lang.Class({
    Name: 'WeblinkListBoxRow',
    Extends: Gtk.Bin,

    templateResource: '/com/endlessm/appstore/eos-app-store-list-row.ui',
    templateChildren: [
        '_mainBox',
        '_icon',
        '_nameLabel',
        '_descriptionLabel',
        '_stateButton',
    ],

    _init: function(model, weblinkId) {
        this.parent();

        this._model = model;
        this._weblinkId = weblinkId;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);
        this._mainBox.show();

        this._stateButton.connect('clicked', Lang.bind(this, this._onStateButtonClicked));
    },

    get weblinkId() {
        return this._weblinkId;
    },

    set weblinkName(name) {
        if (!name)
            name = _("Unknown weblink");

        this._nameLabel.set_text(name);
    },

    set weblinkDescription(description) {
        if (!description)
            description = "";

        this._descriptionLabel.set_text(description);
    },

    set weblinkIcon(name) {
        if (!name)
            name = "gtk-missing-image";

        this._icon.set_from_icon_name(name, Gtk.IconSize.DIALOG);
    },

    set weblinkState(state) {
        this._weblinkState = state;
        this._stateButton.hide();

        switch (this._weblinkState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._stateButton.set_label(_('UNINSTALL'));
                this._stateButton.show();
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._stateButton.set_label(_('INSTALL'));
                this._stateButton.show();
                break;

            default:
                break;
        }
    },

    _onStateButtonClicked: function() {
        switch (this._weblinkState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._model.uninstallWeblink(this._weblinkId);
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._model.installWeblink(this._weblinkId);
                break;
        }
    },
});
Builder.bindTemplateChildren(WeblinkListBoxRow.prototype);

const WeblinkListBox = new Lang.Class({
    Name: 'WeblinkListBox',
    Extends: PLib.ListBox,

    _init: function(model) {
        this.parent();

        this._model = model;
    },
});

const WeblinkDescriptionBox = new Lang.Class({
    Name: 'WeblinkDescriptionBox',
    Extends: Gtk.Frame,

    _init: function() {
        this.parent();
    },
});

const WeblinkFrame = new Lang.Class({
    Name: 'WeblinkFrame',
    Extends: Gtk.Frame,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-frame.ui',
    templateChildren: [
        '_mainBox',
        '_scrolledWindow',
        '_viewport',
    ],

    _init: function() {
        this.parent();

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });

        this._weblinkListModel = new WeblinkListModel.WeblinkList();
        this._weblinkListModel.connect('changed', Lang.bind(this, this._onListModelChange));

        this._stack = new PLib.Stack();
        this._stack.set_transition_duration(250);
        this._stack.set_transition_type(PLib.StackTransitionType.SLIDE_RIGHT);
        this.add(this._stack);
        this._stack.show();

        this._stack.add_named(this._mainBox, 'weblink-list');
        this._mainBox.hexpand = true;
        this._mainBox.vexpand = true;
        this._mainBox.show();

        this._listBox = new WeblinkListBox(this._weblinkListModel);
        this._viewport.add(this._listBox);
        this._listBox.show_all();

        this._descriptionBox = new WeblinkDescriptionBox();
        this._descriptionBox.hexpand = true;
        this._descriptionBox.vexpand = true;
        this._stack.add_named(this._descriptionBox, 'weblink-description');
        this._descriptionBox.show();

        this._stack.set_visible_child_name('weblink-list');
    },

    _onListModelChange: function(model, weblinks) {
        this._listBox.foreach(function(child) { child.destroy(); });

        weblinks.forEach(Lang.bind(this, function(item) {
            let row = new WeblinkListBoxRow(this._weblinkListModel, item);
            row.weblinkName = model.getWeblinkName(item);
            row.weblinkDescription = model.getWeblinkDescription(item);
            row.weblinkIcon = model.getWeblinkIcon(item);
            row.weblinkState = model.getWeblinkState(item);

            this._listBox.add(row);
            row.show();
        }));
    },

    update: function() {
        this._weblinkListModel.update();
    },
});
Builder.bindTemplateChildren(WeblinkFrame.prototype);
