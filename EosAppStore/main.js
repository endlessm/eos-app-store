const AppStore = imports.appStore;
const Environment = imports.environment;

function start() {
    Environment.init();

    return new AppStore.AppStore().run(ARGV);
}
