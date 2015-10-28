//-*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

const AppListModel = imports.appListModel;
const Categories = imports.categories;
const Environment = imports.environment;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Gio = imports.gi.Gio;
const Lang = imports.lang;

const FILL_DESKTOP_NAME = 'com.endlessm.AppStore.FillDesktop';

const FillDesktop = new Lang.Class({
    Name: 'FillDesktop',
    Extends: Gio.Application,

    _init: function() {
        this._appListModel = null;
        this._appInfos = [];

        Environment.loadResources();

        this.parent({ application_id: FILL_DESKTOP_NAME });
    },

    vfunc_activate: function() {
        this.hold();

        this._appListModel = new AppListModel.AppListModel();

        this._appListModel.connect('loading-changed', Lang.bind(this, this._loadAndInstallApps));
    },

    _loadAndInstallApps: function() {
        let appCategories = Categories.get_app_categories();
        for (let category of appCategories) {
            let catId = category.id;
            // INSTALLED is just a pseudo-category; we'll get all the apps by
            // using the other categories already, and then we'll remove from
            // the list those that are already installed with a launcher later.
            if (catId == EosAppStorePrivate.AppCategory.INSTALLED)
                continue;

            this._appInfos = this._appInfos.concat(this._appListModel.loadCategory(catId));
        }

        // Remove apps that are not installed on the device
        // or that already have a launcher
        this._appInfos = this._appInfos.filter(function(app) {
            return !app.get_has_launcher() && app.is_installed();
        });

        let linkCategories = Categories.get_link_categories();
        for (let category of linkCategories) {
            let catId = category.id;
            this._appInfos = this._appInfos.concat(EosAppStorePrivate.link_load_content(catId));
        }

        // Remove links that already have a launcher
        this._appInfos = this._appInfos.filter(function(app) {
            return !this._appListModel.hasLauncher(app.get_desktop_id());
        }, this);
        this._install();
    },

    _install: function() {
        let app = this._appInfos.pop();
        if (!app) {
            this.release();
            return;
        }

        let appId = app.get_desktop_id();
        this._appListModel.install(appId, Lang.bind(this, function(error) {
            this._install();
        }));
    }
});

function main() {
    Environment.init();

    let app = new FillDesktop();
    return app.run(ARGV);
}
