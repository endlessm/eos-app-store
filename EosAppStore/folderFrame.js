// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const Endless = imports.gi.Endless;
const PLib = imports.gi.PLib;

const Builder = imports.builder;
const Lang = imports.lang;

const FolderModel = imports.folderModel;

const _FOLDER_BUTTON_SIZE = 100;

const FolderIconButton = new Lang.Class({
    Name: 'FolderIconButton',
    Extends: Gtk.ToggleButton,

    _init : function(iconName) {
        this.parent({
            active: false,
            'draw-indicator': false,
            'always-show-image': true,
            'width-request': _FOLDER_BUTTON_SIZE,
            'height-request': _FOLDER_BUTTON_SIZE,
            halign: Gtk.Align.START,
            image: new Gtk.Image({'icon-name': iconName}) });

        this._iconName = iconName;
    },
    
    _show_name_bubble: function() {
        let dialog = new Gtk.Dialog({modal: true,
            'transient-for': this.get_toplevel(),
            'focus-on-map': false,
            title: '',
            resizable: false });

        let grid = new Gtk.Grid({orientation: Gtk.Orientation.HORIZONTAL});
        let entry = new Gtk.Entry({'placeholder-text': 'Enter the name of the folder',
                                   'width-chars': 30 });
        let addButton = new Endless.ActionButton({name: 'add',
            'icon-id': 'list-add-symbolic' });

        grid.add(entry);
        grid.add(addButton);
        dialog.get_content_area().add(grid);

        addButton.connect('clicked', Lang.bind(this, function(button) {
            FolderModel.createFolder(entry.get_text(), this._iconName);
            
            dialog.destroy();
            this.set_active(false);
            
            // hide the app store window
            this.get_toplevel().emit('delete-event', null);
        }));
        
        dialog.show_all();
        dialog.run();
        dialog.destroy();
    }
});

const FolderIconGrid = new Lang.Class({
    Name: 'FolderIconGrid',
    Extends: Gtk.Grid,

    _on_button_toggled: function(toggleButton) {
        if (toggleButton.get_active()) {
            for (let i = 0; i < this._toggleButtons.length; i++) {
                let button = this._toggleButtons[i];
        
                if (button != toggleButton && button.get_active()) {
                    button.set_active(false);
                }
            }
            toggleButton._show_name_bubble();
        }
    },
    
    _populate: function(allocatedWidth) {
        this._toggleButtons = [];

        let base = this._path + '/'; 
        let columns = Math.max(1, Math.floor(allocatedWidth / _FOLDER_BUTTON_SIZE));

        for (let i = 0; i < this._iconList.length; i++) {
            let button = new FolderIconButton(this._iconList[i]);

            button.connect('toggled', Lang.bind(this, this._on_button_toggled));
            
            this.attach(button, i % columns, Math.floor(i/columns), 1, 1);
            this._toggleButtons.push(button);
        }
        this.show_all();
    },

    _get_icons: function() {
        this._iconList = FolderModel.getIconList();
        
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

        this._grid = new FolderIconGrid();
        this._viewport.add(this._grid);

        this.show_all();
    }
});
Builder.bindTemplateChildren(FolderFrame.prototype);
