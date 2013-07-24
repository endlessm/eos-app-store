// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GMenu = imports.gi.GMenu;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;

const Lang = imports.lang;
const Path = imports.path;
const Signals = imports.signals;

const AppList = new Lang.Class({
    Name: 'AppList',

    _init: function() {
        this._model = new EosAppStorePrivate.AppListModel();
        this._model.connect('changed', Lang.bind(this, this._onAppListModelChanged));
    },

    update: function() {
        this._model.load(null, Lang.bind(this, this._onLoadComplete));
    },

    _onLoadComplete: function(model, res) {
        try {
            let apps = model.load_finish(res);
            this.emit('changed', apps);
        }
        catch (e) {
            log("Unable to load the application list: " + e);
        }
    },

    _onAppListModelChanged: function() {
        this.update();
    },

    getAppName: function(id) {
        return this._model.get_app_name(id);
    },

    getAppDescription: function(id) {
        return this._model.get_app_description(id);
    },

    getAppIcon: function(id) {
        return this._model.get_app_icon_name(id, EosAppStorePrivate.AppIconState.NORMAL);
    },

    getAppVisible: function(id) {
        return this._model.get_app_visible(id);
    },

    getAppState: function(id) {
        return this._model.get_app_state(id);
    },

    installApp: function(id) {
        this._model.install_app(id);
    },

    uninstallApp: function(id) {
        this._model.uninstall_app(id);
    },

    updateApp: function(id) {
        this._model.update_app(id);
    },
});
Signals.addSignalMethods(AppList.prototype);
