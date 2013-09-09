const Gettext = imports.gettext;

const AppStore = imports.appStore;
const StoreModel = imports.storeModel;

function start() {
    // initialize the global shortcuts for localization
    window._ = Gettext.gettext;
    window.C_ = Gettext.pgettext;
    window.ngettext = Gettext.ngettext;

    let initialPage = StoreModel.StorePage.APPS;
    let args = ARGV;
    for (let i = 0; i < args.length; i++) {
        let arg = args[i];

        if (arg == '--apps' || arg == '-a') {
            initialPage = StoreModel.StorePage.APPS;
            ARGV.splice(i, 1);
            break;
        }

        if (arg == '--web-links' || arg == '-w') {
            initialPage = StoreModel.StorePage.WEB;
            ARGV.splice(i, 1);
            break;
        }

        if (arg == '--folders' || arg == '-f') {
            initialPage = StoreModel.StorePage.FOLDERS;
            ARGV.splice(i, 1);
            break;
        }

        log("Unrecognized argument '" + arg + "'\n" +
            "Usage: eos-app-store [--apps|--folders|--web-links]");
        return -1;
    }

    let app = new AppStore.AppStore(initialPage);
    return app.run(ARGV);
}
