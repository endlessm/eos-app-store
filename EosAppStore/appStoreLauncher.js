// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;

const Lang = imports.lang;

const Config = imports.config;
const Environment = imports.environment;

const APP_STORE_NAME = 'com.endlessm.AppStore';
const APP_STORE_PATH = '/com/endlessm/AppStore';
const APP_STORE_IFACE = 'com.endlessm.AppStore';

const AppStoreIface = '<node><interface name="com.endlessm.AppStore">' +
  '<method name="show">' +
    '<arg type="u" direction="in" name="timestamp"/>' +
    '<arg type="b" direction="in" name="reset"/>' +
  '</method>' +
  '<method name="hide">' +
    '<arg type="u" direction="in" name="timestamp"/>' +
  '</method>' +
  '<method name="showPage">' +
    '<arg type="u" direction="in" name="timestamp"/>' +
    '<arg type="s" direction="in" name="page"/>' +
  '</method>' +
  '<property name="Visible" type="b" access="read"/>' +
'</interface></node>';

const AppStoreProxy = Gio.DBusProxy.makeProxyWrapper(AppStoreIface);

const AppStoreLauncher = new Lang.Class({
    Name: 'AppStoreLauncher',

    _init: function() {
        this.proxy = new AppStoreProxy(Gio.DBus.session,
                                       APP_STORE_NAME,
                                       APP_STORE_PATH,
                                       Lang.bind(this, this._onProxyConstructed));
    },

    _onProxyConstructed: function() {
        log("Launching com.endlessm.AppStore service...");
    }
});

function main() {
    Environment.init();

    let initialPage = 'apps';

    let args = ARGV;
    for (let i in args) {
        let arg = args[i];

        if (arg == '-a' || arg == '--apps') {
            initialPage = 'apps';
            args.splice(i, 1);
            continue;
        }

        if (arg == '-f' || arg == '--folders') {
            initialPage = 'folders';
            args.splice(i, 1);
            continue;
        }

        if (arg == '-w' || arg == '--web-links') {
            initialPage = 'web';
            args.splice(i, 1);
            continue;
        }

        if (arg == '-v' || arg == '--version') {
            log("eos-app-store Version: " + Config.PACKAGE_VERSION);
            return 0;
        }

        if (arg == '-h' || arg == '--help') {
            log("eos-app-store-launcher Version: " + Config.PACKAGE_VERSION + "\n" +
                "\n" +
                "Usage:\n" +
                "  eos-app-store [OPTION...]\n" +
                "\n" +
                "Help options:\n" +
                "  -h, --help           Show help\n" +
                "\n" +
                "Application options:\n" +
                "  -a, --apps           Show the 'Apps' page\n" +
                "  -f, --folders        Show the 'Folders' page\n" +
                "  -w, --web-links      Show the 'Web Links' page\n" +
                "  -v, --version        Print version and exit");
            return 0;
        }

        log("Unknown argument: '" + arg + "'\n" +
            "Usage: eos-app-store-launcher [OPTION...]");
        return -1;
    }

    let storeLauncher = new AppStoreLauncher();
    storeLauncher.proxy.showPageRemote(Gdk.CURRENT_TIME, initialPage);

    return 0;
}
