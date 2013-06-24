const AppStore = imports.appStore;

function start() {
    let app = new AppStore.AppStore();
    return app.run(ARGV);
}
