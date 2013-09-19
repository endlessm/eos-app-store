// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const Lang = imports.lang;
const Signals = imports.signals;

const Path = imports.path;

const StorePage = {
  APPS: 1,
  WEB: 2,
  FOLDERS: 3,
};

const StoreModel = new Lang.Class({
    Name: 'StoreModel',

    _init: function() {
        this._curPage = StorePage.APPS;
    },

    get activePage() {
        return this._curPage;
    },

    changePage: function(newPage) {
        if (this._curPage == newPage) {
            return;
        }

        this._curPage = newPage;
        this.emit('page-changed', this._curPage);
    },
});

Signals.addSignalMethods(StoreModel.prototype);
