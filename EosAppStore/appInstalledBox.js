// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Gtk = imports.gi.Gtk;

const AppInfoBox = imports.appInfoBox;
const Builder = imports.builder;
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

    templateResource: '/com/endlessm/appstore/eos-app-store-app-installed-box.ui',
    templateChildren: [
        '_appIcon',
        '_cancelButton',
        '_controlsSeparator',
        '_controlsStack',
        '_categoryText',
        '_nameText',
        '_overlay',
        '_removeButton',
        '_removeButtonImage',
        '_sizeText',
        '_updateButton',
        '_updateButtonImage',
        '_updateProgressBar',
        '_updateSpinner',
    ],

    _init: function(appInfo) {
        this.parent(appInfo);

        this.initTemplate({ templateRoot: '_overlay', bindChildren: true, connectSignals: true, });
        this.add(this._overlay);

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
                let sizeInMb = size / 1000000;
                /* Translators: Abbreviation for file size in megabytes;
                   %s denotes the placement of the numeric value
                   and can be placed before or after the abbreviation */
                this._sizeText.label = _("%s MB").format(sizeInMb.toFixed(1));
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
Builder.bindTemplateChildren(AppInstalledBox.prototype);
