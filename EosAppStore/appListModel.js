// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const GLib = imports.gi.GLib;

const Lang = imports.lang;
const Path = imports.path;
const Signals = imports.signals;

const EOS_LINK_PREFIX = 'eos-link-';
const EOS_BROWSER = "chromium-browser ";
const EOS_LOCALIZED = "eos-exec-localized ";

const DESKTOP_KEY_SPLASH = 'X-Endless-Splash-Screen';

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

    _replaceAll: function(find, replace, str) {
        return str.replace(new RegExp(find, 'g'), replace);
    },

    _getLocalizedExec: function(args) {
        let languages = GLib.get_language_names();

        // First value is the default one
        let defaultExec = this._replaceAll("^\'|^\"|\'$|\"$", "", args[0]);

        for (let a in args.slice(1)) {
            let arg = args[a];
            let tokens = arg.split(':');
            let key = tokens.shift();
            let value = this._replaceAll("^\'|^\"|\'$|\"$", "", tokens.join(':'));
            for (let l in languages) {
                let language = languages[l];
                if (language == key) {
                    return value;
                }
            }
        }

        return defaultExec;
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

    getWeblinkComment: function(id) {
        return storeList.model.get_app_comment(id);
    },

    getWeblinkUrl: function(id) {
        let exec = storeList.model.get_app_executable(id);
        if (exec.indexOf(EOS_LOCALIZED) == 0) {
            exec = exec.substr(EOS_LOCALIZED.length);
            exec = this._getLocalizedExec(exec.match(/([\w-]+|'(\\'|[^'])*')/g));
        }
        if (exec.indexOf(EOS_BROWSER) == 0) {
            return exec.substr(EOS_BROWSER.length);
        }

        return exec;
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

    createWeblink: function(url, title, icon) {
        let desktop = new GLib.KeyFile();

        // Let's compute a filename
        let filename = url;

        // Skip scheme
        let scheme = GLib.uri_parse_scheme(filename);
        if (scheme) {
            filename = filename.substr((scheme+"://").length);
        }

        // Get only the hostname part
        let tokens = filename.split("/");
        filename = tokens[0];

        // Get only domain name
        tokens = filename.split(".");
        if (tokens.length > 1) {
            filename = tokens[tokens.length-2];
        }

        // Prefix
        filename = "eos-link-" + filename;

        // Append a number until we find a free slot
        let availableFilename = filename + ".desktop";
        let path = GLib.build_filenamev([GLib.get_user_data_dir(), "applications"]);
        let availableFullFilename = GLib.build_filenamev([path, availableFilename]);
        let i = 0;

        while (GLib.file_test(availableFullFilename, GLib.FileTest.EXISTS)) {
            i++;
            availableFilename = filename + "-" + i + ".desktop";
            availableFullFilename = GLib.build_filenamev([path, availableFilename]);
        }

        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_VERSION, "1.0");
        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_TYPE, "Application");
        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_EXEC, EOS_BROWSER + url);
        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_ICON, icon);
        desktop.set_boolean(GLib.KEY_FILE_DESKTOP_GROUP, DESKTOP_KEY_SPLASH, false);
        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_NAME, title);

        let [data, length] = desktop.to_data();
        GLib.file_set_contents(availableFullFilename, data, length);

        return availableFilename;
    },
});
Signals.addSignalMethods(WeblinkList.prototype);
