//-*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
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

    _init: function(onlyApps = false, onlyLinks = false) {
        this._onlyApps = onlyApps;
        this._onlyLinks = onlyLinks;

        this._appListModel = null;
        this._appInfos = [];

        Environment.loadResources();

        this.parent({ application_id: FILL_DESKTOP_NAME });

        this.add_main_option("foobar", 'f'.charCodeAt(0), GLib.OptionArg.NONE, GLib.OptionFlags.NONE, "desc", "arg desc");

        this.connect('handle-local-options', Lang.bind(this, this._parseOptions));
    },

    _parseOptions: function(foo, options) {
        print('options callback');
        print(options.contains("foobar"));
//        print(options.length);
        print("Null testing");
        print(options.lookup_value("foobar", null));
        print("Boolean testing");
        print(options.lookup_value("foobar", Boolean));
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

    let onlyLinks = false;
    let onlyApps = false;

    let args = ARGV;
    for (let arg of []) {
        if (arg == '-l' || arg == '--links-only') {
            if (onlyApps) {
                log("`--apps-only` and `--links-only` are mutually exclusive!");
                return -1;
            }

            onlyLinks = true;
            continue;
        }

        if (arg == '-a' || arg == '--apps-only') {
            if (onlyLinks) {
                log("`--apps-only` and `--links-only` are mutually exclusive!");
                return -1;
            }

            onlyApps = true;
            continue;
        }

        if (arg == '-v' || arg == '--version') {
            log('eos-fill-desktop v' + Config.PACKAGE_VERSION);
            return 0;
        }

        // Fall-through; show help
        log("eos-fill-desktop v" + Config.PACKAGE_VERSION + "\n" +
            "\n" +
            "Usage:\n" +
            "  eos-fill-desktop [OPTION...]\n" +
            "\n" +
            "Help options:\n" +
            "  -h, --help           Show help\n" +
            "\n" +
            "Application options:\n" +
            "  -l, --links-only   Only install links on the desktop\n" +
            "  -a, --apps-only    Only install apps on the desktop\n" +
            "  -v, --version      Print version and exit");

        if (arg == 'help')
            return 0;
        else
            return -1;
    }

    let app = new FillDesktop(onlyApps, onlyLinks);
    return app.run(ARGV);
}
