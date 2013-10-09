// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Endless = imports.gi.Endless;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const Lang = imports.lang;
const Path = imports.path;
const Signals = imports.signals;

const EOS_LINK_PREFIX = 'eos-link-';
const EOS_BROWSER = 'chromium-browser ';
const EOS_LOCALIZED = 'eos-exec-localized ';

const DESKTOP_KEY_SPLASH = 'X-Endless-Splash-Screen';
const DESKTOP_KEY_SHOW_IN_STORE = 'X-Endless-ShowInAppStore';
const DESKTOP_KEY_SHOW_IN_PERSONALITIES = 'X-Endless-ShowInPersonalities';

const StoreModel = new Lang.Class({
    Name: 'StoreModel',

    _init: function() {
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
            let items = model.load_finish(res);
            this.emit('changed', items);
        } catch (e) {
            logError('Unable to load the backing model storage: ' + e);
        }
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

    install: function(id) {
        this._model.install_app(id);
    },

    uninstall: function(id) {
        this._model.uninstall_app(id);
    }
});
Signals.addSignalMethods(BaseList.prototype);

const AppList = new Lang.Class({
    Name: 'AppList',
    Extends: BaseList,

    _onModelChanged: function(model, items) {
        let my_personality = Endless.get_system_personality();

        let apps = items.filter(Lang.bind(this, function(item) {
            if (item.indexOf(EOS_LINK_PREFIX) == 0) {
                // web links are ignored
                return false;
            } else {
                let info = model.model.get_app_info(item);
                return this._isAppVisible(info, my_personality);
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
        let my_personality = Endless.get_system_personality();

        let weblinks = items.filter(Lang.bind(this, function(item) {
            if (item.indexOf(EOS_LINK_PREFIX) == 0) {
                // only take web links into account
                let info = model.model.get_app_info(item);
                return this._isAppVisible(info, my_personality);
            } else {
                return false;
            }
        }));

        this._weblinks = weblinks;
        this._cacheUrls();

        this.emit('changed', weblinks);
    },

    // FIXME: all this code should be removed when the CMS generates
    // non-empty linkId for weblinks.
    // See https://github.com/endlessm/eos-shell/issues/1074
    _cacheUrls: function() {
        // destroy cache
        this._urlsToId = {};

        for (let idx in this._weblinks) {
            let link = this._weblinks[idx];
            let url = this.getWeblinkUrl(link);

            this._urlsToId[url] = link;
        }
    },

    // FIXME: see above
    _replaceAll: function(find, replace, str) {
        return str.replace(new RegExp(find, 'g'), replace);
    },

    // FIXME: see above
    _getLocalizedExec: function(args) {
        let languages = GLib.get_language_names();

        // First value is the default one
        let defaultExec = this._replaceAll('^\'|^\"|\'$|\"$', '', args[0]);

        for (let a in args.slice(1)) {
            let arg = args[a];
            let tokens = arg.split(':');
            let key = tokens.shift();
            let value = this._replaceAll('^\'|^\"|\'$|\"$', '', tokens.join(':'));
            for (let l in languages) {
                let language = languages[l];
                if (language == key) {
                    return value;
                }
            }
        }

        return defaultExec;
    },

    // FIXME: see above
    getWeblinkUrl: function(id) {
        let exec = this._model.get_app_executable(id);
        if (exec.indexOf(EOS_LOCALIZED) == 0) {
            exec = exec.substr(EOS_LOCALIZED.length);
            exec = this._getLocalizedExec(exec.match(/([\w-]+|'(\\'|[^'])*')/g));
        }
        if (exec.indexOf(EOS_BROWSER) == 0) {
            return exec.substr(EOS_BROWSER.length);
        }

        return exec;
    },

    // FIXME: see above
    getWeblinkForUrl: function(url) {
        return this._urlsToId[url];
    },

    getWeblinks: function() {
        return this._weblinks;
    },

    // FIXME: this should use the linkId as provided by the CMS.
    // See https://github.com/endlessm/eos-shell/issues/1074
    createWeblink: function(url, title, icon) {
        let desktop = new GLib.KeyFile();

        // Let's compute a filename
        let filename = url;

        // Skip scheme
        let scheme = GLib.uri_parse_scheme(filename);
        if (scheme) {
            filename = filename.substr((scheme+'://').length);
        }

        // Get only the hostname part
        let tokens = filename.split('/');
        filename = tokens[0];

        // Get only domain name
        tokens = filename.split('.');
        if (tokens.length > 1) {
            filename = tokens[tokens.length-2];
        }

        // Prefix
        filename = 'eos-link-' + filename;

        // Append a number until we find a free slot
        let availableFilename = filename + '.desktop';
        let path = GLib.build_filenamev([GLib.get_user_data_dir(), 'applications']);
        let availableFullFilename = GLib.build_filenamev([path, availableFilename]);
        let i = 0;

        while (GLib.file_test(availableFullFilename, GLib.FileTest.EXISTS)) {
            i++;
            availableFilename = filename + '-' + i + '.desktop';
            availableFullFilename = GLib.build_filenamev([path, availableFilename]);
        }

        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_VERSION, '1.0');
        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_TYPE, 'Application');
        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_EXEC, EOS_BROWSER + url);
        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_ICON, icon);
        desktop.set_boolean(GLib.KEY_FILE_DESKTOP_GROUP, DESKTOP_KEY_SPLASH, false);
        desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_NAME, title);

        let [data, length] = desktop.to_data();
        GLib.file_set_contents(availableFullFilename, data, length);

        return availableFilename;
    }
});
