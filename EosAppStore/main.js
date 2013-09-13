const Gettext = imports.gettext;

const AppStore = imports.appStore;
const StoreModel = imports.storeModel;

function start() {
    // initialize the global shortcuts for localization
    window._ = Gettext.gettext;
    window.C_ = Gettext.pgettext;
    window.ngettext = Gettext.ngettext;

    let app = new AppStore.AppStore(StoreModel.StorePage.APPS);
    return app.run(ARGV);
}
