// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const Lang = imports.lang;
const Path = imports.path;
const Signals = imports.signals;

const BaseList = new Lang.Class({
    Name: 'BaseList',
    Abstract: true,

    _init: function() {
        let application = Gio.Application.get_default();
        this._model = application.appModel;

        this._model.connect('download-progress', Lang.bind(this, this._onDownloadProgress));
        this._model.connect('changed', Lang.bind(this, this._onModelChanged));
        this._onModelChanged(this._model);

        this._cancellables = {};
    },

    _onDownloadProgress: function(model, appid, current, total) {
        // do nothing here
    },

    _onModelChanged: function(model) {
        this.emit('changed');
    },

    hasLauncher: function(id) {
        return this._model.get_app_has_launcher(id);
    },

    install: function(id, callback) {
        if (this._cancellables[id]) {
            log('Installation of app ' + id + ' already in progress.');
            return;
        }

        let application = Gio.Application.get_default();
        application.hold();

        let cancellable = new Gio.Cancellable();
        this._cancellables[id] = cancellable;

        this._model.install_app_async(id, cancellable, Lang.bind(this, function(model, res) {
            this._cancellables[id] = null;

            try {
                this._model.install_app_finish(res);
                if (callback) {
                    callback();
                }
            }
            catch (e) {
                log('Failed to install app ' + id + ': ' + e.message);
                if (callback) {
                    callback(e);
                }
            }

            application.release();
        }));
    },

    cancel: function(id) {
        if (!this._cancellables[id]) {
            return;
        }

        this._cancellables[id].cancel();
    },

    uninstall: function(id, callback) {
        let application = Gio.Application.get_default();
        application.hold();

        this._model.uninstall_app_async(id, null, Lang.bind(this, function(model, res) {
            try {
                this._model.uninstall_app_finish(res);
                if (callback) {
                    callback();
                }
            }
            catch (e) {
                log('Failed to uninstall app ' + id + ': ' + e.message);
                if (callback) {
                    callback(e);
                }
            }

            application.release();
        }));
    },

    refresh: function(callback) {
        let application = Gio.Application.get_default();
        application.hold();

        this._model.refresh_async(null, Lang.bind(this, function(model, res) {
            try {
                this._model.refresh_finish(res);
                if (callback) {
                    callback();
                }
            }
            catch (e) {
                log('Failed to refresh the model: ' + e.message);
                if (callback) {
                    callback(e);
                }
            }

            application.release();
        }));
    }
});
Signals.addSignalMethods(BaseList.prototype);

const AppList = new Lang.Class({
    Name: 'AppList',
    Extends: BaseList,

    _onDownloadProgress: function(model, contentId, current, total) {
        let progress;

        if (current == 0) {
            progress = 0.0;
        }
        else if (current == total) {
            progress = 1.0;
        }
        else {
            progress = current / total;
        }

        this.emit('download-progress', contentId, progress, current, total);
    },

    loadCategory: function(categoryId) {
        return this._model.get_apps_for_category(categoryId);
    },

    updateApp: function(id, callback) {
        if (this._cancellables[id]) {
            log('Update of app ' + id + ' already in progress.');
            return;
        }

        let application = Gio.Application.get_default();
        application.hold();

        let cancellable = new Gio.Cancellable();
        this._cancellables[id] = cancellable;

        this._model.update_app_async(id, cancellable, Lang.bind(this, function(model, res) {
            this._cancellables[id] = null;

            try {
                this._model.update_app_finish(res);
                if (callback) {
                    callback();
                }
            }
            catch (e) {
                log('Failed to update app ' + id + ': ' + e.message);
                if (callback) {
                    callback(e);
                }
            }

            application.release();
        }));
    },

    launch: function(id, timestamp) {
        return this._model.launch_app(id, timestamp);
    }
});

const WeblinkList = new Lang.Class({
    Name: 'WeblinkList',
    Extends: BaseList,
});
