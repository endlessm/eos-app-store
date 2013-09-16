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

    let dir = GLib.get_user_data_dir()+'/desktop-directories';

    // apparently, octal literals are deprecated in JS
    if (GLib.mkdir_with_parents(dir, 0755, null) < 0) {
        log('could not create the directory '+dir);
        return;
    }

    //let fd = GLib.mkstemp_full(dir + '/eos-folder-user-XXXXXX.directory', O_RDWR, 0664);
    let fd = GLib.mkstemp(dir + '/eos-folder-user-XXXXXX.directory');

    if (fd < 0) {
        log('could not create a new file in '+dir);
        return;
    }

    let buf = keyFile.to_data();

    let channel = GLib.IOChannel.unix_new(fd);
    channel.write_chars(buf[0], buf[1]);
    channel.shutdown(true);
};
