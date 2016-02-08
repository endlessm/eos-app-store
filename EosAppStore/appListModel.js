// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Soup = imports.gi.Soup;

const Lang = imports.lang;
const Path = imports.path;
const Signals = imports.signals;

const AppListModel = new Lang.Class({
    Name: 'AppListModel',

    _init: function() {
        EosAppStorePrivate.AppListModel.new_async(null, Lang.bind(this, this._onModelInit));

        this._cancellables = {};
        this._loading = true;

        this._netMonitor = Gio.NetworkMonitor.get_default();
        this._netMonitor.connect('network-changed', Lang.bind(this, this._onNetworkChanged));
        this._networkAvailable = this._netMonitor.get_network_available();
    },

    get loading() {
        return this._loading;
    },

    _onModelInit: function(source, res) {
        try {
            this._model = EosAppStorePrivate.AppListModel.new_finish(res);
        } catch (e) {
            logError(e, 'Error while creating app store model');
            return;
        }

        this._model.connect('changed', Lang.bind(this, this._onModelChanged));

        this._loading = false;
        this.emit('loading-changed');
        this._onModelChanged(this._model);
    },

    _onModelChanged: function(model) {
        this.emit('changed');
    },

    _onNetworkChanged: function() {
        // As a first approximation, we simply check if the network is available
        this._networkAvailable = this._netMonitor.get_network_available();

        // If we cannot get on the network, there's no point in doing any other work
        if (!this._networkAvailable) {
            this.emit('network-changed');
            return;
        }

        // We start an async check to see if we can reach our app server
        let uri = Soup.URI.new(EosAppStorePrivate.get_app_server_url());
        if (!uri) {
            this._networkAvailable = false;
            this.emit('network-changed');
            return;
        }

        let addr = new Gio.NetworkAddress({ hostname: uri.get_host(), port: uri.get_port() });
        this._netMonitor.can_reach_async(addr, null, Lang.bind(this, function(monitor, res) {
            try {
                this._netMonitor.can_reach_finish(res);
                this._networkAvailable = true;
            }
            catch (e) {
                log('Unable to reach app server: ' + e.message);
                this._networkAvailable = false;
            }

            this.emit('network-changed');
        }));
    },

    hasLauncher: function(id) {
        return this._model.get_app_has_launcher(id);
    },

    refresh: function(callback) {
        let application = Gio.Application.get_default();
        application.hold();

        this._model.refresh_network_async(null, Lang.bind(this, function(model, res) {
            try {
                this._model.refresh_network_finish(res);
                if (callback) {
                    callback();
                }
            }
            catch (e) {
                log('Failed to refresh the model from network: ' + e.message);
                if (callback) {
                    callback(e);
                }
            }

            application.release();
        }));
    },

    get networkAvailable() {
        return this._networkAvailable;
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
    },

    loadCategory: function(categoryId) {
        return this._model.get_apps_for_category(categoryId);
    },

    createLink: function(filename) {
        return this._model.create_from_filename(filename);
    },

    updateAppIcon: function(filename) {
        return this._model.update_app_icon_from_filename(filename);
    }
});
Signals.addSignalMethods(AppListModel.prototype);
