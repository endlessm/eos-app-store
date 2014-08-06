// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Endless = imports.gi.Endless;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const Lang = imports.lang;
const Path = imports.path;
const Signals = imports.signals;

const EOS_LINK_PREFIX = 'eos-link-';

const BaseList = new Lang.Class({
    Name: 'BaseList',
    Abstract: true,

    _init: function() {
        let application = Gio.Application.get_default();
        this._model = application.appModel;

        this._model.connect('changed', Lang.bind(this, this._onModelChanged));
        this._onModelChanged(this._model);
    },

    _onModelChanged: function(model) {
        // do nothing here
    },

    getIcon: function(id) {
        return this._model.get_app_icon_name(id);
    },

    getState: function(id) {
        return this._model.get_app_state(id);
    },

    isInstalled: function(id) {
        let appState = this._model.get_app_state(id);

        if (appState == EosAppStorePrivate.AppState.INSTALLED ||
            appState == EosAppStorePrivate.AppState.UPDATABLE) {
            return true;
        }

        return false;
    },

    hasApp: function(id) {
        return this._model.has_app(id);
    },

    hasLauncher: function(id) {
        if (!this.isInstalled(id)) {
            return false;
        }

        return this._model.get_app_has_launcher(id);
    },

    canRemove: function(id) {
        // Only apps that don't have a launcher can be
        // removed from the system
        if (this.hasLauncher(id))
            return false;

        return this._model.get_app_can_remove(id);
    },

    install: function(id, callback) {
        let application = Gio.Application.get_default();
        application.hold();

        this._model.install_app_async(id, null, Lang.bind(this, function(model, res) {
            application.release();

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
        }));
    },

    uninstall: function(id, callback) {
        let application = Gio.Application.get_default();
        application.hold();

        this._model.uninstall_app_async(id, null, Lang.bind(this, function(model, res) {
            application.release();

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
        }));
    }
});
Signals.addSignalMethods(BaseList.prototype);

const AppList = new Lang.Class({
    Name: 'AppList',
    Extends: BaseList,

    _onModelChanged: function(model) {
        let items = model.get_all_apps();
        let apps = items.filter(Lang.bind(this, function(item) {
            if (item.indexOf(EOS_LINK_PREFIX) == 0) {
                // web links are ignored
                return false;
            }

            // TODO: filter language from ID for Endless apps on the server
            return true;
        }));
        this.emit('changed', apps);
    },

    updateApp: function(id, callback) {
        let application = Gio.Application.get_default();
        application.hold();

        this._model.update_app_async(id, null, Lang.bind(this, function(model, res) {
            application.release();

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
        }));
    },

    launch: function(id) {
        return this._model.launch_app(id);
    }
});

const WeblinkList = new Lang.Class({
    Name: 'WeblinkList',
    Extends: BaseList,

    _onModelChanged: function(model) {
        let items = model.get_all_apps();
        let weblinks = items.filter(Lang.bind(this, function(item) {
            if (item.indexOf(EOS_LINK_PREFIX) == -1) {
                // only take web links into account
                return false;
            }

            return true;
        }));
        this.emit('changed', weblinks);
    }
});
