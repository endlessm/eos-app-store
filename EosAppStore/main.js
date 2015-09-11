const AppStore = imports.appStore;
const Environment = imports.environment;

const GLib = imports.gi.GLib;

function start() {
    Environment.init();

    let application = new AppStore.AppStore();
    if (GLib.getenv('EOS_APP_STORE_PERSIST'))
        application.hold();

    try {
        application.register(null);
    } catch (e) {
        logError(e, 'Unable to register app store application');
        return 1;
    }

    if (application.debugWindow) {
        application.activate();
    }

    return application.run(ARGV);
}
