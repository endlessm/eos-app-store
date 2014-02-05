const AppStore = imports.appStore;
const Environment = imports.environment;

const GLib = imports.gi.GLib;

function start() {
    Environment.init();

    let application = new AppStore.AppStore();
    if (GLib.getenv('EOS_APP_STORE_PERSIST'))
        application.hold();
    return application.run(ARGV);
}
