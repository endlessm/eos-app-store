//-*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

const AppListModel = imports.appListModel;
const Categories = imports.categories;
const Environment = imports.environment;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Gettext = imports.gettext;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Lang = imports.lang;

const FILL_DESKTOP_NAME = 'com.endlessm.AppStore.FillDesktop';

const FillDesktop = new Lang.Class({
    Name: 'FillDesktop',
    Extends: Gio.Application,

    _init: function() {
        this._appModel = null;
        this._appList = null;
        this._signalId = null;
        this._appInfos = [];

        Environment.loadResources();

        this.parent({ application_id: FILL_DESKTOP_NAME });
    },

    vfunc_startup: function() {
        this.parent();

        this._appModel = new AppListModel.StoreModel();
    },

    vfunc_activate: function() {
        this.hold();
        this._appList = new AppListModel.AppList();
        this._signalId = this._appList.connect('changed', Lang.bind(this, this._onChanged));
    },

    _onChanged: function() {
        this._appList.disconnect(this._signalId);

        let categories = Categories.get_app_categories();
        for (let c in categories) {
            let category = categories[c].id;

            this._appInfos = this._appInfos.concat(EosAppStorePrivate.app_load_content(category, null));
        }

        categories = Categories.get_link_categories();
        for (let c in categories) {
            let category = categories[c].id;

            this._appInfos = this._appInfos.concat(EosAppStorePrivate.link_load_content(category));
        }

        // Remove elements without ID or already installed
        this._appInfos = this._appInfos.filter(Lang.bind(this, function(app) {
            let appId = app.get_desktop_id();
            if (!appId) {
                return false;
            }

            let state = this._appList.getState(appId);
            if (state == EosAppStorePrivate.AppState.UNINSTALLED) {
                return true;
            } else {
                return false;
            }
        }));

        this._install();
    },

    _install: function() {
        let app = this._appInfos.pop();
        if (!app) {
            this.release();
            return;
        }

        let appId = app.get_desktop_id();

        this._appList.install(appId, Lang.bind(this, function(model, res) {
            try {
                model.install_app_finish(res);
                this._install();
            } catch (e) {
                this._install();
            }
        }));
    },

    get appModel() {
        return this._appModel;
    }
});

function main() {
    // initialize the global shortcuts for localization
    window._ = Gettext.gettext;
    window.C_ = Gettext.pgettext;
    window.ngettext = Gettext.ngettext;

    let app = new FillDesktop();
    return app.run(ARGV);
}
