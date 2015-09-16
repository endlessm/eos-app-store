// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gdk = imports.gi.Gdk;
const Gtk = imports.gi.Gtk;
const Cairo = imports.cairo;

const AppStorePages = imports.appStorePages;
const Builder = imports.builder;
const Lang = imports.lang;
const FolderModel = imports.folderModel;
const Separator = imports.separator;

const _FOLDER_BUTTON_IMAGE_SIZE = 64;
const _FOLDER_BUTTON_SIZE = 96;
const _FOLDER_GRID_SPACING = 32;
const _FOLDER_GRID_BORDER = _FOLDER_GRID_SPACING / 2;

const _BUBBLE_ENTRY_WIDTH_CHARS = 15;
const _BUBBLE_GRID_SPACING = 6;
const _ADD_FOLDER_BUTTON_SIZE = 30;

const FolderNameBubble = new Lang.Class({
    Name: 'FolderNameBubble',
    Extends: Gtk.Popover,

    _init : function(folderModel) {
        this.parent({ position: Gtk.PositionType.BOTTOM });
        this.get_style_context().add_class('folder-bubble');

        this._folderModel = folderModel;

        let border = new Gtk.Frame();
        border.get_style_context().add_class('bubble-border');

        let grid = new Gtk.Grid({
            column_spacing: _BUBBLE_GRID_SPACING });

        // entry and "add" button...

        this._entry = new Gtk.Entry({
            placeholder_text: _("Name of folder"),
            width_chars: _BUBBLE_ENTRY_WIDTH_CHARS,
            hexpand: true,
            halign: Gtk.Align.FILL,
            vexpand: true,
            valign: Gtk.Align.FILL,
            no_show_all: true });
        this._addButton = new Gtk.Button({
            width_request: _ADD_FOLDER_BUTTON_SIZE,
            height_request: _ADD_FOLDER_BUTTON_SIZE,
            hexpand: false,
            vexpand: true,
            valign: Gtk.Align.CENTER,
            no_show_all: true });

        this._entry.connect('changed', Lang.bind(this, function() {
            this._addButton.set_sensitive(this._entry.get_text().trim().length != 0);
        }));

        this._entry.connect('activate',
                            Lang.bind(this, this._createFolderFromEntry));

        this._addButton.connect('clicked',
                                Lang.bind(this, this._createFolderFromEntry));

        // ... which will be replaced by "done" label and icon

        this._doneLabel = new Gtk.Label({
            label: _("Folder added!"),
            hexpand: true,
            halign: Gtk.Align.CENTER,
            vexpand: true,
            valign: Gtk.Align.CENTER,
            name: 'doneLabel',
            no_show_all: true  });
        this._addedIcon = new Gtk.Image({
            resource: '/com/endlessm/appstore/icon_installed_24x24.png',
            width_request: _ADD_FOLDER_BUTTON_SIZE,
            height_request: _ADD_FOLDER_BUTTON_SIZE,
            hexpand: false,
            vexpand: true,
            valign: Gtk.Align.CENTER,
            no_show_all: true
        });

        grid.attach(this._entry, 0, 0, 1, 1);
        grid.attach(this._addButton, 1, 0, 1, 1);

        grid.attach(this._doneLabel, 0, 1, 1, 1);
        grid.attach(this._addedIcon, 1, 1, 1, 1);

        border.add(grid);
        this.add(border);
        border.show_all();

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
        if (this._entry.get_text().trim().length != 0) {
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
    Extends: Gtk.RadioButton,

    _init : function(group, iconName) {
        this.parent({
            active: false,
            draw_indicator: false,
            group: group,
            always_show_image: true,
            width_request: _FOLDER_BUTTON_SIZE,
            height_request: _FOLDER_BUTTON_SIZE,
            relief: Gtk.ReliefStyle.NONE,
            hexpand: false,
            vexpand: false,
            halign: Gtk.Align.CENTER,
            image: new Gtk.Image({
                icon_name: iconName,
                pixel_size: _FOLDER_BUTTON_IMAGE_SIZE }) });

        this._iconName = iconName;
        this.get_style_context().add_class('folder-icon-button');
    }
});

const FolderIconGrid = new Lang.Class({
    Name: 'FolderIconGrid',
    Extends: Gtk.FlowBox,

    _init: function(folderModel) {
        this.parent({
            row_spacing: _FOLDER_GRID_SPACING,
            column_spacing: _FOLDER_GRID_SPACING,
            border_width: _FOLDER_GRID_BORDER,
            selection_mode: Gtk.SelectionMode.NONE });

        this._folderModel = folderModel;
        this._bubble = null;
        this._buttonToggled = false;

        this.get_style_context().add_class('folder-icon-grid');

        // FIXME: we need to listen for keypress events in the grid to allow
        // switching the focus and start inserting the text automatically,
        // when the user starts typing, WITHOUT removing the placeholder text.
        // This won't be necessary when GTK+ allows setting the focus to a
        // GtkEntry without removing the hint while no text has been inserted.
        this.add_events(Gdk.EventMask.KEY_PRESS_MASK);
        this.connect('key-press-event', Lang.bind(this, this._onKeyPress));

        // Create an additional (hidden) GtkRadioButton; this makes it so
        // there's no initial selection in the group. Othwewise the first
        // FolderIconButton in the group would be pre-selected and ignore
        // clicks on it.
        this._buttonGroup = new Gtk.RadioButton();

        let iconList = this._folderModel.getIconList();
        for (let i = 0; i < iconList.length; i++) {
            let button = new FolderIconButton(this._buttonGroup, iconList[i]);

            button.connect('toggled', Lang.bind(this, this._onButtonToggled));
            this.add(button);
        }

        this.show_all();
    },

    _onButtonToggled: function(toggleButton) {
        if (!toggleButton.get_active()) {
            return;
        }

        // hide any bubble we might have previously created.
        // Note that calling hide() will immediately trigger
        // the 'closed' callback
        if (this._bubble != null) {
            this._buttonToggled = true;
            this._bubble.hide();
            this._buttonToggled = false;
        }

        // bubble window
        this._bubble = new FolderNameBubble(this._folderModel);
        this._bubble.connect('closed', Lang.bind(this, function() {
            // reset selection if we're not toggling another button
            if (!this._buttonToggled) {
                this._buttonGroup.set_active(true);
            }
            this._bubble = null;
        }));

        // prepare the bubble window for showing...
        this._bubble._iconName = toggleButton._iconName;
        this._bubble.setEntryVisible(true);
        this._bubble._entry.set_text('');
        this._bubble._addButton.set_sensitive(false);
        this._bubble.relative_to = toggleButton;

        // ... and now we show the bubble, grabbing the input
        this._bubble.show();
    },

    _onKeyPress : function(window, event) {
        if (this._bubble != null && !this._bubble.has_focus) {
            this._bubble.grab_focus();
            this._bubble.event(event);
        }

        return false;
    }
});

const FolderFrame = new Lang.Class({
    Name: 'FolderFrame',
    Extends: Gtk.Frame,
    Implements: [AppStorePages.AppStorePageProvider],

    templateResource: '/com/endlessm/appstore/eos-app-store-folder-frame.ui',
    templateChildren: [
        '_folderBoxContent',
        '_mainBox',
        '_scrolledWindow',
        '_viewport',
    ],

    _init: function() {
        this.parent({ visible: true });

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.get_style_context().add_class('folder-frame');
        this.add(this._mainBox);

        this._folderModel = new FolderModel.FolderModel();
        this._grid = null;

        let separator = new Separator.FrameSeparator();
        this._folderBoxContent.add(separator);
        this._folderBoxContent.reorder_child(separator, 1);
    },

    createPage: function() {
        return this;
    },

    getIcon: function() {
        return 'resource:///com/endlessm/appstore/icon_folder-symbolic.svg';
    },

    getPageIds: function() {
        return ['folders'];
    },

    getName: function() {
        return _("Folders");
    },

    getTitle: function() {
        return _("Install folders");
    },

    populate: function() {
        if (this._grid) {
            return;
        }

        this._grid = new FolderIconGrid(this._folderModel);
        this._viewport.add(this._grid);

        this.show_all();
    },

    reset: function() {
        let vscrollbar = this._scrolledWindow.get_vscrollbar();
        vscrollbar.set_value(0);
    }
});
Builder.bindTemplateChildren(FolderFrame.prototype);
