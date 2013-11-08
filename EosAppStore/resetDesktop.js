//-*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-

const ShellAppStore = imports.shellAppStore;

function main() {
    let shellProxy = new ShellAppStore.ShellAppStore();
    shellProxy.proxy.ResetDesktopSync();
}
