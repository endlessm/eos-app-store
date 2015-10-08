// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;
const Pango = imports.gi.Pango;

const AppInfoBox = imports.appInfoBox;
const Categories = imports.categories;
const Lang = imports.lang;

const UPDATING_OPACITY = 0.3;
const NORMAL_OPACITY = 1.0;

const AppInstalledBoxRow = new Lang.Class({
    Name: 'AppInstalledBoxRow',
    Extends: Gtk.ListBoxRow,

    _init: function(appInfo) {
        this.parent();

        let installedBox = new AppInstalledBox(appInfo);
        installedBox.connect('destroy', Lang.bind(this, this.destroy));
        this.add(installedBox);
        installedBox.show();
    }
});

const AppInstalledBox = new Lang.Class({
    Name: 'AppInstalledBox',
    Extends: AppInfoBox.AppBaseBox,

    _init: function(appInfo) {
        this.parent(appInfo);

        this._overlay = new Gtk.Overlay();
        this.add(this._overlay);

        let mainBox = new Gtk.Box({ spacing: 10,
                                    height_request: 54 });
        mainBox.get_style_context().add_class('installed-app-box');
        this._overlay.add(mainBox);

        this._appIcon = new Gtk.Image({ use_fallback: true,
                                        icon_size: Gtk.IconSize.DIALOG,
                                        margin_start: 7,
                                        margin_top: 7,
                                        margin_bottom: 7,
                                        margin_end: 1 });
        mainBox.add(this._appIcon);

        let descriptionBox = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL,
                                           hexpand: true,
                                           valign: Gtk.Align.CENTER,
                                           spacing: 8 });
        mainBox.add(descriptionBox);

        this._nameText = new Gtk.Label({ ellipsize: Pango.EllipsizeMode.END,
                                         width_chars: 20,
                                         max_width_chars: 40,
                                         lines: 1,
                                         xalign: 0,
                                         expand: true });
        this._nameText.get_style_context().add_class('app-name');
        descriptionBox.add(this._nameText);

        this._categoryText = new Gtk.Label({ width_chars: 20,
                                             max_width_chars: 40,
                                             lines: 1,
                                             xalign: 0,
                                             expand: true });
        this._categoryText.get_style_context().add_class('app-category');
        descriptionBox.add(this._categoryText);

        this._controlsStack = new Gtk.Stack();
        mainBox.add(this._controlsStack);

        let box = new Gtk.Box();
        this._controlsStack.add_named(box, 'controls');

        this._controlsBox = new Gtk.Box({ spacing: 12 });
        this._controlsBox.get_style_context().add_class('controls-box');
        box.add(this._controlsBox);

        this._updateButtonImage = new Gtk.Frame({ width_request: 16,
                                                  height_request: 16,
                                                  valign: Gtk.Align.CENTER });
        this._updateButtonImage.get_style_context().add_class('state-image');

        this._updateButton = new Gtk.Button({ valign: Gtk.Align.CENTER,
                                              child: this._updateButtonImage });
        this._updateButton.connect('clicked', Lang.bind(this, this._onUpdateButtonClicked));
        this._updateButton.get_style_context().add_class('state-button');
        this._updateButton.get_style_context().add_class('update');
        this._controlsBox.add(this._updateButton);

        this._controlsSeparator = new Gtk.Separator({ orientation: Gtk.Orientation.VERTICAL });
        this._controlsSeparator.get_style_context().add_class('controls-separator');
        this._controlsBox.add(this._controlsSeparator);

        this._removeButtonImage = new Gtk.Frame({ width_request: 16,
                                                  height_request: 16,
                                                  valign: Gtk.Align.CENTER });
        this._removeButtonImage.get_style_context().add_class('state-image');

        this._removeButton = new Gtk.Button({ valign: Gtk.Align.CENTER,
                                              child: this._removeButtonImage });
        this._removeButton.connect('clicked', Lang.bind(this, this._onRemoveButtonClicked));
        this._removeButton.get_style_context().add_class('state-button');
        this._removeButton.get_style_context().add_class('remove');
        this._controlsBox.add(this._removeButton);

        this._sizeText = new Gtk.Label({ label: _("SIZE"),
                                         ellipsize: Pango.EllipsizeMode.END,
                                         margin_end: 10,
                                         width_chars: 15,
                                         max_width_chars: 15,
                                         xalign: 1 });
        this._sizeText.get_style_context().add_class('app-size');
        box.add(this._sizeText);

        let box2 = new Gtk.Box();
        box2.get_style_context().add_class('controls-box');
        this._controlsStack.add_named(box2, 'spinner');

        this._updateSpinner = new Gtk.Spinner();
        box2.add(this._updateSpinner);

        let updateLabel = new Gtk.Label ({ label: _("UPDATING…"),
                                           max_width_chars: 10 });
        updateLabel.get_style_context().add_class('app-updating');
        box2.add(updateLabel);

        let cancelButtonImage = new Gtk.Image({ icon_size: Gtk.IconSize.MENU,
                                                icon_name: 'process-stop-symbolic' });

        let cancelButton = new Gtk.Button({ valign: Gtk.Align.CENTER,
                                            child: cancelButtonImage });
        cancelButton.connect('clicked', Lang.bind(this, this._onCancelButtonClicked));
        cancelButton.get_style_context().add_class('state-button');
        cancelButton.get_style_context().add_class('cancel');
        box2.add(cancelButton);

        this._updateProgressBar = new Gtk.ProgressBar({ hexpand: true,
                                                        valign: Gtk.Align.END,
                                                        no_show_all: true });
        this._updateProgressBar.get_style_context().add_class('update-progress-bar');
        this._overlay.add_overlay(this._updateProgressBar);

        this.show_all();

        this.appIcon = this.appInfo.get_icon_name();
        this.nameText = this.appTitle;
        this.categoryText = this.appInfo.get_category();

        this._sizeId = this.appInfo.connect('notify::installed-size', Lang.bind(this, this._updateSize));
        this._updateSize();

        this._removeDialog = null;

        this.setImageFrame(this._removeButton, this._removeButtonImage);
        this.setImageFrame(this._updateButton, this._updateButtonImage);

        this._syncState();
    },

    _onDestroy: function() {
        this.parent();

        if (this._sizeId > 0) {
            this.appInfo.disconnect(this._sizeId);
            this._sizeId = 0;
        }
    },

    set appIcon(v) {
        this._appIcon.set_from_icon_name(v, Gtk.IconSize.DIALOG);
    },

    set nameText(v) {
        this._nameText.label = v;
    },

    set categoryText(v) {
        let categories = Categories.get_app_categories();
        for (let i in categories) {
            let category = categories[i];

            if (category.id == v) {
                this._categoryText.label = category.label.toUpperCase();
                return;
            }
        }

        // If we got here, we hit an unknown category
        log('Unknown category id "' + v + '"');
        this._categoryText.hide();
    },

    _updateSize: function() {
        if (this.appInfo.is_store_installed()) {
            let size = this.appInfo.get_installed_size();
            if (size == 0) {
                this._sizeText.label = '--';
            } else {
                this._sizeText.label = GLib.format_size(size);
            }
        } else {
                this._sizeText.label = _("System App");
        }
    },

    _syncState: function() {
        // Hide all controls, and show only what's needed
        this._updateButton.hide();
        this._removeButton.hide();
        this._controlsSeparator.hide();

        if (this.model.networkAvailable && this.appInfo.is_updatable()) {
            this._updateButton.show();
            this._controlsSeparator.show();
        }

        if (this.appInfo.is_removable()) {
            this._removeButton.show();
        }

        this._syncUpdateState();
    },

    _syncUpdateState: function() {
        if (this.appInfo.is_updating()) {
            this._appIcon.opacity = UPDATING_OPACITY;
            this._nameText.opacity = UPDATING_OPACITY;
            this._categoryText.opacity = UPDATING_OPACITY;

            this._updateProgressBar.show();
            this._updateSpinner.start();
            this._controlsStack.visible_child_name = 'spinner';
        } else {
            this._appIcon.opacity = NORMAL_OPACITY;
            this._nameText.opacity = NORMAL_OPACITY;
            this._categoryText.opacity = NORMAL_OPACITY;

            this._updateProgressBar.hide();
            this._updateSpinner.stop();
            this._controlsStack.visible_child_name = 'controls';
        }
    },

    _downloadProgress: function(progress, current, total) {
        this._updateProgressBar.fraction = progress;
    },

    _onUpdateButtonClicked: function() {
        this.doUpdate();
    },

    _onRemoveButtonClicked: function() {
        let responseId = this.showRemoveDialog();

        if (responseId == Gtk.ResponseType.APPLY) {
            this.doRemove(Lang.bind(this, function(error) {
                if (!error) {
                    this.destroy();
                }
            }));
        }
    },

    _onCancelButtonClicked: function() {
        this.doCancel();
    }
});
