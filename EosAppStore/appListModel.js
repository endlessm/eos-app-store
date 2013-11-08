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
const DESKTOP_KEY_SHOW_IN_PERSONALITIES = 'X-Endless-ShowInPersonalities';

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

    _isAppVisible: function(info, personality) {
        if (info.has_key(DESKTOP_KEY_SHOW_IN_STORE) && info.get_boolean(DESKTOP_KEY_SHOW_IN_STORE)) {
            if (info.has_key(DESKTOP_KEY_SHOW_IN_PERSONALITIES)) {
                let personalities = info.get_string(DESKTOP_KEY_SHOW_IN_PERSONALITIES);

                if (personalities && personalities.length > 0) {
                    if (!personality) {
                        // the application requires specific personalities but this system doesn't have one
                        return false;
                    }
                    let split = personalities.split(';');
                    for (let i = 0; i < split.length; i++) {
                        if (split[i].toLowerCase() == personality.toLowerCase()) {
                            // the system's personality matches one of the app's
                            return true;
                        }
                    }
                    return false;
                }
            }

            // if the key is not set, or is set but empty, the app will be shown
            return true;
        }

        // the application will not be shown in the app store unless
        // its desktop entry has X-Endless-ShowInAppStore=true
        return false;
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
        return this._model.get_app_icon_name(id, EosAppStorePrivate.AppIconState.NORMAL);
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

    install: function(id, callback) {
        this._model.install_app_async(id, null, callback);
    },

    uninstall: function(id, callback) {
        this._model.uninstall_app_async(id, null, callback);
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
        let myPersonality = Endless.get_system_personality();

        let apps = items.filter(Lang.bind(this, function(item) {
            if (item.indexOf(EOS_LINK_PREFIX) == 0) {
                // web links are ignored
                return false;
            } else {
                let info = model.model.get_app_info(item);
                return this._isAppVisible(info, myPersonality);
            }
        }));
        this._apps = apps;
        this.emit('changed', this._apps);
    },

    updateApp: function(id) {
        this._model.update_app(id);
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
        let myPersonality = Endless.get_system_personality();

        let weblinks = items.filter(Lang.bind(this, function(item) {
            if (item.indexOf(EOS_LINK_PREFIX) == 0) {
                // only take web links into account
                let info = model.model.get_app_info(item);
                return this._isAppVisible(info, myPersonality);
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
