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
