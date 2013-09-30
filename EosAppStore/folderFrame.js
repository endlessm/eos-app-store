// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gdk = imports.gi.Gdk;
const Gtk = imports.gi.Gtk;
const PLib = imports.gi.PLib;
const Cairo = imports.cairo;

const Builder = imports.builder;
const Lang = imports.lang;

const FolderModel = imports.folderModel;

const _FOLDER_BUTTON_SIZE = 64;
const _FOLDER_GRID_SPACING = _FOLDER_BUTTON_SIZE;
const _FOLDER_GRID_BORDER = _FOLDER_GRID_SPACING / 2;

const _BUBBLE_GRID_SPACING = 6;
const _ADD_FOLDER_BUTTON_SIZE = 30;

const FolderNameBubble = new Lang.Class({
    Name: 'FolderNameBubble',
    Extends: PLib.BubbleWindow,

    _init : function(folderModel) {
        this.parent();
        this.get_style_context().add_class('folder-bubble');

        this._folderModel = folderModel;

        let grid = new Gtk.Grid({
            'column-spacing': _BUBBLE_GRID_SPACING });

        // entry and "add" button...

        this._entry = new Gtk.Entry({
            'placeholder-text': _("Enter the name of the folder"),
            'width-chars': 30,
            hexpand: true,
            halign: Gtk.Align.FILL,
            vexpand: true,
            valign: Gtk.Align.FILL,
            'no-show-all': true });
        this._addButton = new Gtk.Button({
            'width-request': _ADD_FOLDER_BUTTON_SIZE,
            'height-request': _ADD_FOLDER_BUTTON_SIZE,
            hexpand: false,
            vexpand: true,
            valign: Gtk.Align.CENTER,
            'no-show-all': true });

        this._entry.connect('changed', Lang.bind(this, function() {
            this._addButton.set_sensitive(this._entry.get_text_length() != 0);
        }));

        this._entry.connect('activate',
                            Lang.bind(this, this._createFolderFromEntry));

        this._addButton.connect('clicked',
                                Lang.bind(this, this._createFolderFromEntry));

        // ... which will be replaced by "done" label and icon

        this._doneLabel = new Gtk.Label({
            label: _("The new folder has been added"),
            hexpand: true,
            halign: Gtk.Align.CENTER,
            vexpand: true,
            valign: Gtk.Align.CENTER,
            'no-show-all': true  });
        this._addedIcon = new Gtk.Image({
            resource: '/com/endlessm/appstore/icon_installed_24x24.png',
            'width-request': _ADD_FOLDER_BUTTON_SIZE,
            'height-request': _ADD_FOLDER_BUTTON_SIZE,
            hexpand: false,
            vexpand: true,
            valign: Gtk.Align.CENTER,
            'no-show-all': true
        });

        grid.attach(this._entry, 0, 0, 1, 1);
        grid.attach(this._addButton, 1, 0, 1, 1);

        grid.attach(this._doneLabel, 0, 1, 1, 1);
        grid.attach(this._addedIcon, 1, 1, 1, 1);

        grid.show();
        this.add(grid);

        this.connect('key-press-event', Lang.bind(this, this._onKeyPress));
    },

    _onKeyPress : function(window, event) {
        if (!this._entry.has_focus) {
            this._entry.grab_focus();
            // Append rather than overwrite
            this._entry.set_position(this._entry.get_text_length());
        }

        return false;
    },

    _createFolderFromEntry : function() {
        if (this._entry.get_text_length() != 0) {
            this._folderModel.createFolder(this._entry.get_text(),
                                           this._iconName);
            this.setEntryVisible(false);
        }
    },

    setEntryVisible : function(visible) {
        if (visible) {
            // Temporarily hide the entry, then show the bubble window,
            // so that the placeholder text is displayed
            this._entry.hide();
            this.show();

            this._doneLabel.hide();
            this._addedIcon.hide();
            this._entry.show();
            this._addButton.show();
            this.get_style_context().remove_class('done');
            this.get_style_context().add_class('entering');
        } else {
            this._entry.hide();
            this._addButton.hide()
            this._doneLabel.show();
            this._addedIcon.show();
            this.get_style_context().remove_class('entering');
            this.get_style_context().add_class('done');
        }
    }
});

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
            relief: Gtk.ReliefStyle.NONE,
            hexpand: false,
            vexpand: false,
            image: new Gtk.Image({'icon-name': iconName}) });

        this._iconName = iconName;
    }
});

const FolderIconGrid = new Lang.Class({
    Name: 'FolderIconGrid',
    Extends: Gtk.Grid,

    _on_button_toggled: function(toggleButton) {
        if (toggleButton.get_active()) {
            let oldToggle = this._activeToggle;
            this._activeToggle = toggleButton;

            // unset the previous one
            if (oldToggle && oldToggle != toggleButton && oldToggle.get_active()) {
                oldToggle.set_active(false);
            }

            // prepare the bubble window for showing...
            this._bubble._iconName = toggleButton._iconName;
            this._bubble.setEntryVisible(true);
            this._bubble._entry.set_text('');
            this._bubble._addButton.set_sensitive(false);

            // ... and now we show the bubble and grab the input
            this._bubble.popup(toggleButton.get_window(),
                               toggleButton.get_allocation(),
                               Gtk.PositionType.BOTTOM);

            let display = Gdk.Display.get_default();
            let devicemgr = display.get_device_manager();
            let device = devicemgr.get_client_pointer();
            this._bubble.grab(device, Gdk.CURRENT_TIME);
        }
    },

    _populate: function(allocatedWidth) {
        this._toggleButtons = [];

        let base = this._path + '/';
        let columns = Math.max(1, Math.floor(allocatedWidth / (_FOLDER_BUTTON_SIZE + _FOLDER_GRID_SPACING)));

        for (let i = 0; i < this._iconList.length; i++) {
            let button = new FolderIconButton(this._iconList[i]);

            button.connect('toggled', Lang.bind(this, this._on_button_toggled));

            this.attach(button, i % columns, Math.floor(i/columns), 1, 1);
            this._toggleButtons.push(button);
        }
        this.show_all();
    },

    _get_icons: function() {
        this._iconList = this._folderModel.getIconList();

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
            let handler = this.connect('size-allocate',
                                       Lang.bind(this, function (widget, allocation) {
                                           this.disconnect(handler);
                                           this._populate(allocation.width);
                                       }));
        }
    },

    _init: function(folderModel) {
        this.parent({
            'row-spacing': _FOLDER_GRID_SPACING,
            'column-spacing': _FOLDER_GRID_SPACING,
            'border-width': _FOLDER_GRID_BORDER });

        this._folderModel = folderModel;
        this._get_icons();
        this._activeToggle = null;

        // bubble window

        this._bubble = new FolderNameBubble(folderModel);

        this._bubble.connect('hide', Lang.bind(this, function() {
            this._activeToggle.set_active(false);
            this._activeToggle = null;
        }));
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

        this._folderModel = new FolderModel.FolderModel();

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.get_style_context().add_class('folder-frame');

        this._mainBox.hexpand = true;
        this._mainBox.vexpand = true;

        this.add(this._mainBox);

        this._grid = new FolderIconGrid(this._folderModel);
        this._viewport.add(this._grid);

        this.show_all();
    },

    reset: function() {
    }
});
Builder.bindTemplateChildren(FolderFrame.prototype);
