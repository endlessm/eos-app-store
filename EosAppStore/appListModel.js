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
const EOS_BROWSER = 'chromium-browser ';
const EOS_LOCALIZED = 'eos-exec-localized ';

const DESKTOP_KEY_SHOW_IN_STORE = 'X-Endless-ShowInAppStore';

const StoreModel = new Lang.Class({
    Name: 'StoreModel',

    _init: function() {
        this._items = [];

        this.model= new EosAppStorePrivate.AppListModel();
        this.model.connect('changed', Lang.bind(this, this._onModelChanged));

        // initialize model state
        this._updating = false;
        this.update();
    },

    update: function() {
        if (this._updating) {
            return;
        }

        this._updating = true;
        this.model.load(null, Lang.bind(this, this._onLoadComplete));
    },

    _onModelChanged: function() {
        this.update();
    },

    _onLoadComplete: function(model, res) {
        this._updating = false;
        try {
            this._items = model.load_finish(res);
            this.emit('changed', this._items);
        } catch (e) {
            this._items = [];
            logError('Unable to load the backing model storage: ' + e);
        }
    },

    getItems: function() {
        return this._items;
    }
});
Signals.addSignalMethods(StoreModel.prototype);

const BaseList = new Lang.Class({
    Name: 'BaseList',
    Abstract: true,

    _init: function() {
        let application = Gio.Application.get_default();
        this._storeModel = application.appModel;
        this._model = this._storeModel.model;

        this._storeModel.connect('changed', Lang.bind(this, this._onModelChanged));
        this._onModelChanged(this._storeModel, this._storeModel.getItems());
    },

    _onModelChanged: function(appModel, items) {
        // do nothing here
    },

    _isAppVisible: function(info) {
        return info.get_boolean(DESKTOP_KEY_SHOW_IN_STORE);
    },

    update: function() {
        this._storeModel.update();
    },

    getName: function(id) {
        return this._model.get_app_name(id);
    },

    getDescription: function(id) {
        return this._model.get_app_description(id);
    },

    getIcon: function(id) {
        return this._model.get_app_icon_name(id);
    },

    getComment: function(id) {
        return this._model.get_app_comment(id);
    },

    getState: function(id) {
        return this._model.get_app_state(id);
    },

    getVisible: function(id) {
        return this._model.get_app_visible(id);
    },

    isInstalled: function(id) {
        let appState = this._model.get_app_state(id);

        if (appState == EosAppStorePrivate.AppState.INSTALLED ||
            appState == EosAppStorePrivate.AppState.UPDATABLE) {
            return true;
        }

        return false;
    },

    hasLauncher: function(id) {
        if (!this.isInstalled(id)) {
            return false;
        }

        return this._model.get_app_has_launcher(id);
    },

    install: function(id, callback) {
        this._model.install_app_async(id, null, Lang.bind(this, function(model, res) {
            try {
                this._model.install_app_finish(res);
                callback();
            }
            catch (e) {
                log('Failed to install app ' + e.message);
                callback(e);
            }
        }));
    },

    uninstall: function(id, callback) {
        this._model.uninstall_app_async(id, null, Lang.bind(this, function(model, res) {
            try {
                this._model.uninstall_app_finish(res);
                callback();
            }
            catch (e) {
                log('Failed to uninstall app ' + e.message);
                callback(e);
            }
        }));
    }
});
Signals.addSignalMethods(BaseList.prototype);

const AppList = new Lang.Class({
    Name: 'AppList',
    Extends: BaseList,

    _init: function() {
        this._apps = [];
        this.parent();
    },

    _onModelChanged: function(model, items) {
        let apps = items.filter(Lang.bind(this, function(item) {
            if (item.indexOf(EOS_LINK_PREFIX) == 0) {
                // web links are ignored
                return false;
            }

            let info = model.model.get_app_info(item);
            if (info) {
                return this._isAppVisible(info);
            }

            // TODO: filter language from ID for Endless apps on the server
            return true;
        }));
        this._apps = apps;
        this.emit('changed', this._apps);
    },

    updateApp: function(id) {
        this._model.update_app_async(id, null, Lang.bind(this, function(model, res) {
            try {
                this._model.update_app_finish(res);
                callback();
            }
            catch (e) {
                log('Failed to update app ' + e.message);
                callback(e);
            }
        }));
    },

    launch: function(id) {
        return this._model.launch_app(id);
    },

    get apps() {
        return this._apps;
    },
});

const WeblinkList = new Lang.Class({
    Name: 'WeblinkList',
    Extends: BaseList,

    _init: function() {
        this._weblinks = [];
        this._urlsToId = {};

        this.parent();
    },

    _onModelChanged: function(model, items) {
        let weblinks = items.filter(Lang.bind(this, function(item) {
            if (item.indexOf(EOS_LINK_PREFIX) == 0) {
                // only take web links into account
                let info = model.model.get_app_info(item);
                return this._isAppVisible(info);
            } else {
                return false;
            }
        }));

        this._weblinks = weblinks;

        this.emit('changed', weblinks);
    },

    getWeblinks: function() {
        return this._weblinks;
    }
});
