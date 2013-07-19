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
    },

    update: function() {
        this._model.load(null, Lang.bind(this, this._onLoadComplete));
    },

    _onLoadComplete: function(model, res) {
        let apps = model.load_finish(res);

        this._apps = apps;
        this.emit('changed', this._apps);
    },

    getAppInfo: function(id) {
        if (!this._apps || !this._apps[id]) {
            return null;
        }

        let entry = this._apps[id];
        return entry.get_app_info();
    },

    getAppName: function(id) {
        let info = this.getAppInfo(id);
        if (!info) {
            return "Unknown";
        }

        return info.get_generic_name(info);
    },

    getAppDescription: function(id) {
        return "Generic application description to be filled out by the manifest";
    },

    getNoDisplay: function(id) {
        let info = this.getAppInfo(id);
        if (!info) {
            return true;
        }

        return info.get_nodisplay() || info.get_is_hidden();
    },
});
Signals.addSignalMethods(AppList.prototype);
