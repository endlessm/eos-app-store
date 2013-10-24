//-*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

const AppListModel = imports.appListModel;
const Categories = imports.categories;
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
        this._appInfos = [];

        this.parent({ application_id: FILL_DESKTOP_NAME });
    },

    vfunc_startup: function() {
        this.parent();

        this._appModel = new AppListModel.StoreModel();
        this._appList = new AppListModel.AppList();
    },

    vfunc_activate: function() {
        let categories = Categories.get_app_categories();
        for (let c in categories) {
            let category = categories[c].id;

            this._appInfos = this._appInfos.concat(EosAppStorePrivate.app_load_content(category));
        }

        categories = Categories.get_link_categories();
        for (let c in categories) {
            let category = categories[c].id;

            this._appInfos = this._appInfos.concat(EosAppStorePrivate.link_load_content(category));
        }

        this._install();
        this.hold();
    },

    _install: function() {
        let app = this._appInfos.pop();
        if (!app) {
            this.release();
            return;
        }

        let appId = app.get_desktop_id();
        if (!appId) {
            this._install();
            return;
        }

        // Check if it is already installed
        let state =  this._appList.getState(appId);
        if (state == EosAppStorePrivate.AppState.INSTALLED) {
            this._install();
            return;
        }

        try {
            this._appList.install(appId, Lang.bind(this, function(model, res) {
                model.install_app_finish(res);
                this._install();
            }));
        } catch (e) {
            this._install();
        }
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
