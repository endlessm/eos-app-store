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

function createFolder(label, iconName) {
    print('Add folder '+label+' with icon '+iconName);
};
