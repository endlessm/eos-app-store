// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const PLib = imports.gi.PLib;

const Builder = imports.builder;
const Lang = imports.lang;
const Signals = imports.signals;
const Path = imports.path;

const _FOLDER_BUTTON_SIZE = 100;

const FolderIconGrid = new Lang.Class({
    Name: 'FolderIconGrid',
    Extends: Gtk.Grid,

    _on_button_toggled: function(toggleButton) {
        if (toggleButton.get_active()) {
            // unset the other buttons
            for (let i = 0; i < this._toggleButtons.length; i++) {
                let button = this._toggleButtons[i];
                if (button != toggleButton && button.get_active()) {
                    button.set_active(false);
                }
            }
        }
    },
    
    _populate: function(allocatedWidth) {
        this._toggleButtons = [];

        let base = this._path + '/'; 
        let columns = Math.max(1, Math.floor(allocatedWidth / _FOLDER_BUTTON_SIZE));

        for (let i = 0; i < this._iconFiles.length; i++) {
            let button = new Gtk.ToggleButton({
                active: false,
                'draw-indicator': false,
                'always-show-image': true,
                'width-request': _FOLDER_BUTTON_SIZE,
                'height-request': _FOLDER_BUTTON_SIZE,
                halign: Gtk.Align.START,
                image: new Gtk.Image({file: base + this._iconFiles[i].get_name()}) });

            button.connect('toggled', Lang.bind(this, this._on_button_toggled));
            
            this.attach(button, i % columns, Math.floor(i/columns), 1, 1);
            this._toggleButtons.push(button);
        }
        this.show_all();
    },

    _get_icons: function() {
        let dir =  Gio.File.new_for_path(this._path);
        this._iconFiles = [];
        
        let enumerator = dir.enumerate_children('standard::name,standard::display-name',
                                                Gio.FileQueryInfoFlags.NONE,
                                                null, null);
        
        for (let f = enumerator.next_file(null, null); f != null; f = enumerator.next_file(null, null)) {
            // TODO : check the type of the file, it should be an image
            this._iconFiles.push(f)
        }
        enumerator.close(null);
        
        // TODO better solution needed here
        // wait for allocation to know how many columns the grid should have
        if (this.get_realized()) {
            // the widget has been allocated already
            GLib.idle_add(GLib.PRIORITY_HIGH_IDLE,
                          Lang.bind(this, this._populate),
                          this.get_allocated_width());
        }
        else {
            // we will populate it when it is allocated
            let handler = this.connect("size-allocate",
                                       Lang.bind(this, function (widget, allocation) {
                                           this.disconnect(handler);
                                           this._populate(allocation.width);
                                       }));
        }
    },

    _init: function(path) {
        this.parent();

        this._path = path;
        this._get_icons();
    }
});

const FolderFrame = new Lang.Class({
    Name: 'FolderFrame',
    Extends: Gtk.Frame,

    templateResource: '/com/endlessm/appstore/eos-app-store-folder-frame.ui',
    templateChildren: [
        '_mainBox',
        '_scrolledWindow',
        '_viewport',
    ],

    _init: function() {
        this.parent();

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.get_style_context().add_class('folder-frame');

        this._mainBox.hexpand = true;
        this._mainBox.vexpand = true;

        this.add(this._mainBox);

        this._grid = new FolderIconGrid(Path.FOLDER_ICONS_DIR);
        this._viewport.add(this._grid);

        this.show_all();
    }
});
Builder.bindTemplateChildren(FolderFrame.prototype);
