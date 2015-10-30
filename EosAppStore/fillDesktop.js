//-*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Lang = imports.lang;

const AppListModel = imports.appListModel;
const Config = imports.config;
const Categories = imports.categories;
const Environment = imports.environment;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;

const FILL_DESKTOP_NAME = 'com.endlessm.AppStore.FillDesktop';

const FillDesktop = new Lang.Class({
    Name: 'FillDesktop',
    Extends: Gio.Application,

    _init: function() {
        this._appListModel = null;
        this._appInfos = [];

        Environment.loadResources();

        this.parent({ application_id: FILL_DESKTOP_NAME });

        this.add_main_option('apps-only', 'a'.charCodeAt(0), GLib.OptionArg.NONE,
                             GLib.OptionFlags.NONE,
                             "Only install apps on the desktop",
                             null);

        this.add_main_option('links-only', 'l'.charCodeAt(0), GLib.OptionArg.NONE,
                             GLib.OptionFlags.NONE,
                             "Only install web links on the desktop",
                             null);

        this.add_main_option('version', 'v'.charCodeAt(0), GLib.OptionArg.NONE,
                             GLib.OptionFlags.NONE,
                             "Print version and exit",
                             null);

        this.connect('handle-local-options', Lang.bind(this, this._parseOptions));
    },

    _parseOptions: function(foo, options) {
        if (options.contains('version')) {
            print('eos-fill-desktop v' + Config.PACKAGE_VERSION);
            return 0;
        }

        this._onlyApps = options.contains('apps-only');
        this._onlyLinks = options.contains('links-only');

        if (this._onlyApps && this._onlyLinks) {
            print("`--apps-only` and `--links-only` are mutually exclusive!");
            return 1;
        }

        return 0;
    },

    vfunc_activate: function() {
        this.hold();

        this._appListModel = new AppListModel.AppListModel();

        this._appListModel.connect('loading-changed', Lang.bind(this, this._loadAndInstallApps));
    },

    _loadAndInstallApps: function() {
        if (!this._onlyLinks) {
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
            this._appInfos = this._appInfos.filter(app =>
                !app.get_has_launcher() && app.is_installed()
            );
        }

        if (!this._onlyApps) {
            let linkCategories = Categories.get_link_categories();
            for (let category of linkCategories) {
                let catId = category.id;
                this._appInfos = this._appInfos.concat(EosAppStorePrivate.link_load_content(catId));
            }

            // Remove links that already have a launcher
            this._appInfos = this._appInfos.filter(a =>
                !this._appListModel.hasLauncher(a.get_desktop_id())
            );
        }

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

    let args = ARGV;

    // Strip `--` from calling script
    args.shift();
    // Add script invocation name
    args.unshift('eos-fill-desktop');

    let app = new FillDesktop();
    return app.run(args);
}
