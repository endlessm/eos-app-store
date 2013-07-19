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

        this._model.load(null, Lang.bind(this, this._onLoadComplete));
    },

    _onLoadComplete: function(model, res) {
        let apps = model.load_finish(res);

        for (let a in apps) {
            log("Loaded app '" + a + "'");
        }
    },
});
