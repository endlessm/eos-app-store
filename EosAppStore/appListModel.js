// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;

const Lang = imports.lang;
const Path = imports.path;
const Signals = imports.signals;

const EOS_LINK_PREFIX = 'eos-link-';

var storeList = null;

const StoreList = new Lang.Class({
    Name: 'StoreList',

    _init: function() {
        this.model = new EosAppStorePrivate.AppListModel();
        this.model.connect('changed', Lang.bind(this, this._onAppListModelChanged));

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

    _onLoadComplete: function(model, res) {
        this._updating = false;
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

});
Signals.addSignalMethods(StoreList.prototype);

const AppList = new Lang.Class({
    Name: 'AppList',

    _init: function() {
        this._apps = null;
        if (!storeList) {
            storeList = new StoreList();
        }
        storeList.connect('changed', Lang.bind(this, this._onStoreListChanged));
    },

    _onStoreListChanged: function(store, allItems) {
        let apps = allItems.filter(function(item) {
            return item.indexOf(EOS_LINK_PREFIX) != 0;
        });
        this.emit('changed', apps);
    },

    update: function() {
        storeList.update();
    },

    getAppName: function(id) {
        return storeList.model.get_app_name(id);
    },

    getAppDescription: function(id) {
        return storeList.model.get_app_description(id);
    },

    getAppIcon: function(id) {
        return storeList.model.get_app_icon_name(id, EosAppStorePrivate.AppIconState.NORMAL);
    },

    getAppVisible: function(id) {
        return storeList.model.get_app_visible(id);
    },

    getAppState: function(id) {
        return storeList.model.get_app_state(id);
    },

    installApp: function(id) {
        storeList.model.install_app(id);
    },

    uninstallApp: function(id) {
        storeList.model.uninstall_app(id);
    },

    updateApp: function(id) {
        storeList.model.update_app(id);
    },
});
Signals.addSignalMethods(AppList.prototype);

const WeblinkList = new Lang.Class({
    Name: 'WeblinkList',

    _init: function() {
        if (!storeList) {
            storeList = new StoreList();
        }
        storeList.connect('changed', Lang.bind(this, this._onStoreListChanged));
    },

    _onStoreListChanged: function(store, allItems) {
        let weblinks = allItems.filter(function(item) {
            return item.indexOf(EOS_LINK_PREFIX) == 0;
        });
        this.emit('changed', weblinks);
    },

    update: function() {
        storeList.update();
    },

    getWeblinkName: function(id) {
        return storeList.model.get_app_name(id);
    },

    getWeblinkDescription: function(id) {
        return storeList.model.get_app_description(id);
    },

    getWeblinkIcon: function(id) {
        return storeList.model.get_app_icon_name(id, EosAppStorePrivate.AppIconState.NORMAL);
    },

    getWeblinkState: function(id) {
        return storeList.model.get_app_state(id);
    },

    installWeblink: function(id) {
        storeList.model.install_app(id);
    },

    uninstallWeblink: function(id) {
        storeList.model.uninstall_app(id);
    },
});
Signals.addSignalMethods(WeblinkList.prototype);
