// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const Config = imports.config;
const Gettext = imports.gettext;
const Path = imports.path;

function init() {
    Gettext.bindtextdomain(Config.GETTEXT_PACKAGE, Path.LOCALE_DIR);
    Gettext.textdomain(Config.GETTEXT_PACKAGE);

    // initialize the global shortcuts for localization
    window._ = Gettext.gettext;
    window.C_ = Gettext.pgettext;
    window.ngettext = Gettext.ngettext;

    GLib.set_prgname('eos-app-store');
    GLib.set_application_name(_("Application Store"));
}

function loadResources() {
    let resources =
        [[Path.RESOURCE_DIR, 'eos-app-store.gresource'],
         [Path.CONTENT_DIR, 'eos-app-store-app-content.gresource'],
         [Path.CONTENT_DIR, 'eos-app-store-link-content.gresource']];

    for (let idx in resources) {
        let path = GLib.build_filenamev(resources[idx]);
        let resource = Gio.Resource.load(path);
        resource._register();
    }
}
