// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;

const Lang = imports.lang;

var CategoryButton = new Lang.Class({
    Name: 'CategoryButton',
    Extends: Gtk.RadioButton,
    Properties: { 'category': GObject.ParamSpec.string('category',
                                                       'Category',
                                                       'The category name',
                                                       GObject.ParamFlags.READABLE |
                                                       GObject.ParamFlags.WRITABLE |
                                                       GObject.ParamFlags.CONSTRUCT,
                                                       ''),
                  'index': GObject.ParamSpec.int('index',
                                                 'Index',
                                                 'The button index',
                                                 GObject.ParamFlags.READABLE |
                                                 GObject.ParamFlags.WRITABLE |
                                                 GObject.ParamFlags.CONSTRUCT,
                                                 0, GLib.MAXINT32, 0) },
    _init: function(params) {
        this._category = '';
        this._index = 0;

        this.parent(params);

        this.get_style_context().add_class('category-button');
    },

    get category() {
        return this._category;
    },

    set category(c) {
        if (this._category == c) {
            return;
        }

        this._category = c;
        this.notify('category');
    },

    get index() {
        return this._index;
    },

    set index(i) {
        if (this._index == i) {
            return;
        }

        this._index = i;
        this.notify('index');
    }
});
