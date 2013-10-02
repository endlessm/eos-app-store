// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;

const Lang = imports.lang;

const CategoryButton = new Lang.Class({
    Name: 'CategoryButton',
    Extends: Gtk.RadioButton,
    Properties: { 'category': GObject.ParamSpec.string('category',
                                                       'Category',
                                                       'The category name',
                                                       GObject.ParamFlags.READABLE |
                                                       GObject.ParamFlags.WRITABLE |
                                                       GObject.ParamFlags.CONSTRUCT,
                                                       '') },
    _init: function(params) {
        this._category = '';

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
    }
});
