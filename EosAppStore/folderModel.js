//-*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const Lang = imports.lang;

const _PREFIX = 'eos-folder';

function getIconList() {
    let iconTheme = Gtk.IconTheme.get_default();

    // TODO specify a context?
    let allIcons = iconTheme.list_icons(null);

    let folderIcons = [];
    for (let i = 0; i < allIcons.length; i++) {
        if (allIcons[i].indexOf(_PREFIX) == 0) {
            folderIcons.push(allIcons[i]);
        }
    }
    return folderIcons;
};

function createFolder(name, iconName) {
    let keyFile = new GLib.KeyFile();

    keyFile.set_value(GLib.KEY_FILE_DESKTOP_GROUP,
                     GLib.KEY_FILE_DESKTOP_KEY_NAME, name);

    keyFile.set_value(GLib.KEY_FILE_DESKTOP_GROUP,
                     GLib.KEY_FILE_DESKTOP_KEY_ICON, iconName);

    keyFile.set_value(GLib.KEY_FILE_DESKTOP_GROUP,
                     GLib.KEY_FILE_DESKTOP_KEY_TYPE, GLib.KEY_FILE_DESKTOP_TYPE_DIRECTORY);

    let dirpath = GLib.get_user_data_dir()+'/desktop-directories';

    // apparently, octal literals are deprecated in JS
    if (GLib.mkdir_with_parents(dirpath, 0755, null) < 0) {
        log('could not create the directory '+dirpath);
        return;
    }

    let dir =  Gio.File.new_for_path(dirpath);

    let enumerator = dir.enumerate_children('standard::name',
                                            Gio.FileQueryInfoFlags.NONE, null);

    let prefix = 'eos-folder-user-';
    let suffix = '.directory';
    let re = new RegExp(prefix + '[0-9]+' + suffix);
    let n = -1;

    for (let f = enumerator.next_file(null); f != null; f = enumerator.next_file(null)) {
        let name = f.get_name();
        if (re.test(name)) {
            let new_n = name.slice(name.indexOf(prefix) + prefix.length,
                                   name.indexOf(suffix));
            n = Math.max(n, parseInt(new_n));
        }
    }
    enumerator.close(null);

    let filename = prefix + (n+1) + suffix;

    let buf = keyFile.to_data();

    let channel = GLib.IOChannel.new_file(dirpath + '/' + filename, 'w');
    channel.write_chars(buf[0], buf[1]);
    channel.shutdown(true);
};
