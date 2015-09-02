// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Mainloop = imports.mainloop;

const AppListModel = imports.appListModel;
const AppStoreWindow = imports.appStoreWindow;
const Builder = imports.builder;
const Categories = imports.categories;
const Lang = imports.lang;
const Notify = imports.notify;
const Separator = imports.separator;
const Signals = imports.signals;

const AppInstalledBox = new Lang.Class({
    Name: 'AppInstalledBox',
    Extends: Gtk.Bin,

    templateResource: '/com/endlessm/appstore/eos-app-store-app-installed-box.ui',
    templateChildren: [
        '_mainBox',
        '_appIcon',
        '_nameText',
        '_categoryText',
        '_controlsBox',
        '_updateButton',
        '_updateButtonImage',
        '_removeButton',
        '_removeButtonImage',
        '_sizeText',
    ],

    _init: function(model, appInfo) {
        this.parent();

        let app = Gio.Application.get_default();
        let mainWindow = app.mainWindow;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);

        this._model = model;
        this._appInfo = appInfo;

        this.appIcon = this._appInfo.get_icon_name();
        this.nameText = this._appInfo.get_title();
        this.categoryText = this._appInfo.get_category();
        this.sizeText = this._appInfo.get_installed_size();

        this._removeDialog = null;

        this._windowHideId = mainWindow.connect('hide', Lang.bind(this, this._destroyPendingDialogs));
        this.connect('destroy', Lang.bind(this, this._onDestroy));

        this._networkAvailable = this._model.networkAvailable;
        this._networkChangeId = this._model.connect('network-changed', Lang.bind(this, this._onNetworkMonitorChanged));

        this._updateControlsState();
    },

    set appIcon(v) {
        this._appIcon.set_icon_name(v, Gtk.IconSize.DIALOG);
    },

    set nameText(v) {
        this._nameText.label = v;
    },

    set categoryText(v) {
        let categories = Categories.get_app_categories();
        for (let i in categories) {
            let category = categories[i];

            if (category.id == v) {
                this._categoryText.label = category.label;
                return;
            }
        }

        // If we got here, we hit an unknown category
        log('Unknown category id "' + v + '"');
        this._categoryText.hide();
    },

    set sizeText(v) {
        if (v == 0) {
            this._sizeText.hide();
        } else {
            this._sizeText.label = GLib.format_size(v);
            this._sizeText.show();
        }
    },

    _onNetworkMonitorChanged: function() {
        this._networkAvailable = this._model.networkAvailable;
        this._updateControlsState();
    },

    _destroyRemoveDialog: function() {
        if (this._removeDialog != null) {
            this._removeDialog.destroy();
            this._removeDialog = null;
        }
    },

    _destroyPendingDialogs: function() {
        this._destroyRemoveDialog();
    },

    _onDestroy: function() {
        this._destroyPendingDialogs();

        if (this._windowHideId != 0) {
            let app = Gio.Application.get_default();
            let appWindow = app.mainWindow;

            if (appWindow) {
                appWindow.disconnect(this._windowHideId);
            }

            this._windowHideId = 0;
        }

        if (this._networkChangeId != 0) {
            this._model.disconnect(this._networkChangeId);
            this._networkChangeId = 0;
        }
    },

    _updateControlsState: function() {
        // Hide all controls, and show only what's needed
        this._updateButton.hide();
        this._buttonSeparator.hide();
        this._removeButton.hide();

        if (this._networkAvailable && this._appInfo.is_updatable()) {
            this._updateButton.show();
            this._buttonSeparator.show();
        }

        if (this._appInfo.is_removable()) {
            this._removeButton.show();
        }
    },

    _onUpdateButtonClicked: function() {
        let app = Gio.Application.get_default();
        app.pushRunningOperation();

        this._model.updateApp(this._appId, Lang.bind(this, function(error) {
            app.popRunningOperation();

            if (error) {
                app._maybeNotifyUser(_("We could not update '%s'").format(this._appInfo.get_title()), error);
                return;
            }

            app.maybeNotifyUser(_("'%s' was updated successfully").format(this._appInfo.get_title()));

            this._updateControlsState();
        }));
    },

    _onRemoveButtonClicked: function() {
        let dialog = new Gtk.MessageDialog({ set_transient_for: app.mainWindow,
                                             modal: true,
                                             destroy_with_parent: true,
                                             text: _("Deleting app"),
                                             secondary_text: _("Deleting this app will remove it "
                                                               "from the device for all users. You "
                                                               "will need to download it from the "
                                                               "internet in order to reinstall it." });
        let applyButton = dialog.add_button(_("Delete app"), Gtk.ResponseType.APPLY);
        applyButton.get_style_context().add_class('destructive-action');
        dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL);
        dialog.show_all();
        this._removeDialog = dialog;

        let responseId = this._removeDialog.run();
        this._destroyRemoveDialog();

        if (responseId == Gtk.ResponseType.APPLY) {
            let app = Gio.Application.get_default();
            app.pushRunningOperation();

            this._model.uninstall(this._appId, Lang.bind(this, function(error) {
                app.popRunningOperation();

                if (error) {
                    app.maybeNotifyUser(_("We could not remove '%s'").format(this.appTitle), error);
                    return;
                }

                app.maybeNotifyUser(_("'%s' was removed successfully").format(this.appTitle));

                // Remove ourselves from the list
                this.destroy();
            }));
        }
    },
});
Builder.bindTemplateChildren(AppInstalledBox.prototype);
