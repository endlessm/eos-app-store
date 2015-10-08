// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Gio = imports.gi.Gio;
const Gtk = imports.gi.Gtk;

const AppStoreWindow = imports.appStoreWindow;
const Builder = imports.builder;
const Lang = imports.lang;
const Separator = imports.separator;

const SCREENSHOT_LARGE = 480;
const SCREENSHOT_SMALL = 120;

const AppPreview = new Lang.Class({
    Name: 'AppPreviewImage',
    Extends: Gtk.EventBox,

    _init: function(path, width) {
        this.parent();

        this._path = path;

        this._image = new Gtk.Image();
        this.add(this._image);

        EosAppStorePrivate.app_load_screenshot(this._image, this._path, width);
    },

    get path() {
        return this._path;
    },
});

const AppBaseBox = new Lang.Class({
    Name: 'AppBaseBox',
    Extends: Gtk.Bin,

    _init: function(appInfo) {
        this.parent();

        let app = Gio.Application.get_default();
        let mainWindow = app.mainWindow;
        this._model = app.appListModel;
        this._appInfo = appInfo;

        this._networkChangeId = this._model.connect('network-changed', Lang.bind(this, this._syncState));
        this._progressId = this._appInfo.connect('download-progress', Lang.bind(this, this._onDownloadProgress));
        this._stateChangedId = this._appInfo.connect('notify::state', Lang.bind(this, this._syncState));
        this._windowHideId = mainWindow.connect('hide', Lang.bind(this, this._destroyPendingDialogs));

        this._removeDialog = null;

        this.connect('destroy', Lang.bind(this, this._onDestroy));
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

        if (this._stateChangedId != 0) {
            this._appInfo.disconnect(this._stateChangedId);
            this._stateChangedId = 0;
        }

        if (this._progressId != 0) {
            this._appInfo.disconnect(this._progressId);
            this._progressId = 0;
        }

        if (this._networkChangeId != 0) {
            this._model.disconnect(this._networkChangeId);
            this._networkChangeId = 0;
        }
    },

    _onDownloadProgress: function(appInfo, current, total) {
        let progress;

        if (current == 0) {
            progress = 0.0;
        }
        else if (current == total) {
            progress = 1.0;
        }
        else {
            progress = current / total;
        }

        this._downloadProgress(progress, current, total);
    },

    _downloadProgress: function() {
        // to be overridden
    },

    _syncState: function() {
        // to be overridden
    },

    get appInfo() {
        return this._appInfo;
    },

    get appId() {
        return this._appInfo.get_desktop_id();
    },

    get appTitle() {
        return this._appInfo.get_title();
    },

    get model() {
        return this._model;
    },

    setImageFrame: function(button, imageFrame) {
        button.connect('state-flags-changed', function() {
            // We use the background-image of a GtkFrame to set the image,
            // and we need to forward the state flags to it, since GtkFrame
            // can't track hover/active alone
            let stateFlags = button.get_state_flags();
            imageFrame.set_state_flags(stateFlags, true);
        });
    },

    _pushTransaction: function() {
        let app = Gio.Application.get_default();
        app.pushRunningOperation();
    },

    _popTransaction: function() {
        let app = Gio.Application.get_default();
        app.popRunningOperation();
    },

    showRemoveDialog: function() {
        let app = Gio.Application.get_default();
        let dialog = new Gtk.MessageDialog({ transient_for: app.mainWindow,
                                             modal: true,
                                             destroy_with_parent: true,
                                             text: _("Deleting app"),
                                             secondary_text: _("Deleting this app will remove it " +
                                                               "from the device for all users. You " +
                                                               "will need to download it from the " +
                                                               "internet in order to reinstall it.") });
        let applyButton = dialog.add_button(_("Delete app"), Gtk.ResponseType.APPLY);
        applyButton.get_style_context().add_class('destructive-action');
        dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL);
        dialog.show_all();
        this._removeDialog = dialog;

        let responseId = this._removeDialog.run();
        this._destroyRemoveDialog();

        return responseId;
    },

    doRemove: function(callback) {
        this._pushTransaction();

        this._model.uninstall(this.appId, Lang.bind(this, function(error) {
            this._popTransaction();

            let app = Gio.Application.get_default();

            if (error) {
                app.maybeNotifyUser(_("We could not remove '%s'").format(this.appTitle), error);
            }
            else {
                app.maybeNotifyUser(_("'%s' was removed successfully").format(this.appTitle));
            }

            this._syncState();

            if (callback) {
                callback(error);
            }
        }));
    },

    doUpdate: function(callback) {
        this._pushTransaction();

        this._model.updateApp(this.appId, Lang.bind(this, function(error) {
            this._popTransaction();

            let app = Gio.Application.get_default();

            if (error) {
                app.maybeNotifyUser(_("We could not update '%s'").format(this.appTitle), error);
            }
            else {
                app.maybeNotifyUser(_("'%s' was updated successfully").format(this.appTitle));
            }

            this._syncState();

            if (callback) {
                callback(error);
            }
        }));
    },

    doInstall: function(callback) {
        this._pushTransaction();

        this.model.install(this.appId, Lang.bind(this, function(error) {
            this._popTransaction();

            let app = Gio.Application.get_default();

            if (error) {
                app.maybeNotifyUser(_("We could not install '%s'").format(this.appTitle), error);
            }
            else {
                app.maybeNotifyUser(_("'%s' was installed successfully").format(this.appTitle));
            }

            this._syncState();

            if (!error) {
                let app = Gio.Application.get_default();
                let appWindow = app.mainWindow;
                if (!app.debugWindow && appWindow && appWindow.is_visible()) {
                    appWindow.hide();
                }
            }

            if (callback) {
                callback(error);
            }
        }));
    },

    doCancel: function() {
        this.model.cancel(this.appId);
    }
});

const AppInfoBox = new Lang.Class({
    Name: 'AppInfoBox',
    Extends: AppBaseBox,

    templateResource: '/com/endlessm/appstore/eos-app-store-app-info-box.ui',
    templateChildren: [
        '_contentBox',
        '_descriptionText',
        '_installButton',
        '_installButtonImage',
        '_installButtonLabel',
        '_installProgress',
        '_installProgressBar',
        '_installProgressCancel',
        '_installProgressLabel',
        '_installProgressSpinner',
        '_mainBox',
        '_removeButton',
        '_removeButtonImage',
        '_removeButtonLabel',
        '_screenshotImage',
        '_screenshotPreviewBox',
    ],

    _init: function(appInfo) {
        this.parent(appInfo);

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);

        let app = Gio.Application.get_default();
        let mainWindow = app.mainWindow;
        let width = mainWindow.getExpectedWidth();
        width = Math.max(width, AppStoreWindow.AppStoreSizes.VGA.screenWidth);
        let xgaWidth = AppStoreWindow.AppStoreSizes.XGA.screenWidth;
        if (width < xgaWidth) {
            let screenshotRatio = SCREENSHOT_SMALL / SCREENSHOT_LARGE;
            this._screenshotLarge = SCREENSHOT_LARGE + width - xgaWidth;
            this._screenshotSmall = this._screenshotLarge * screenshotRatio;
        } else {
            this._screenshotLarge = SCREENSHOT_LARGE;
            this._screenshotSmall = SCREENSHOT_SMALL;
        }

        this.appDescription = this.appInfo.get_description();
        this.appScreenshots = this.appInfo.get_screenshots();

        this.setImageFrame(this._installButton, this._installButtonImage);
        this.setImageFrame(this._removeButton, this._removeButtonImage);

        let separator = new Separator.FrameSeparator();
        this._mainBox.add(separator);
        this._mainBox.reorder_child(separator, 0);
        this._mainBox.show();

        this._syncState();
    },

    _syncState: function() {
        this.appState = this.appInfo.get_state();
    },

    _showInstallSpinner: function() {
        let label = this._appInfo.is_updating() ?
            _("Updating…") : _("Installing…");
        this._installProgressLabel.set_text(label);
        this._installProgressSpinner.show();
        this._installProgressSpinner.start();
        this._installProgressBar.hide();
    },

    _downloadProgress: function(progress, current, total) {
        if (current == total) {
            this._showInstallSpinner();
            return;
        }

        this._installProgressSpinner.hide();
        this._installProgressBar.show();
        this._installProgressBar.fraction = progress;
    },

    set appDescription(description) {
        if (!description) {
            description = "";
        }

        this._descriptionText.buffer.text = description;
    },

    set appScreenshots(screenshots) {
        this._screenshotPreviewBox.hide();
        this._screenshotImage.hide();

        this._screenshotPreviewBox.foreach(Lang.bind(this, function (smallScreenshot) {
            smallScreenshot.destroy();
        }));

        for (let i in screenshots) {
            let path = screenshots[i];

            if (i == 0) {
                EosAppStorePrivate.app_load_screenshot(this._screenshotImage,
                                                       path,
                                                       this._screenshotLarge);
            }

            let previewBox = new AppPreview(path, this._screenshotSmall);
            this._screenshotPreviewBox.add(previewBox);
            previewBox.connect('button-press-event', Lang.bind(this, this._onPreviewPress));
        }

        if (screenshots && screenshots.length > 0) {
            this._screenshotPreviewBox.show_all();
        }
    },

    _onPreviewPress: function(widget, event) {
        EosAppStorePrivate.app_load_screenshot(this._screenshotImage, widget.path, this._screenshotLarge);
        return false;
    },

    _setStyleClassFromState: function() {
        const INSTALL = 0;
        const UPDATE = 1;
        const ADD = 2;
        const LAUNCH = 3;
        let style = INSTALL;

        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                if (this.appInfo.get_has_launcher()) {
                    style = LAUNCH;
                }
                else {
                    style = ADD;
                }
                break;

            case EosAppStorePrivate.AppState.AVAILABLE:
                style = INSTALL;
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                if (this.appInfo.get_has_launcher()) {
                    style = UPDATE;
                }
                else {
                    style = ADD;
                }
                break;
        }

        let context = this._installButton.get_style_context();

        switch (style) {
            case INSTALL:
            case ADD:
                // Use the default install class for either of these
                context.remove_class('update');
                context.remove_class('launch');
                break;

            case UPDATE:
                context.remove_class('launch');
                context.add_class('update');
                break;

            case LAUNCH:
                context.remove_class('update');
                context.add_class('launch');
                break;
        }
    },

    set appState(state) {
        this._appState = state;

        this._setStyleClassFromState();

        // start from a hidden state
        this._installButton.hide();
        this._removeButton.hide();

        const BUTTON_LABEL_INSTALL = _("Install app");
        const BUTTON_LABEL_UPDATE = _("Update app");
        const BUTTON_LABEL_LAUNCH = _("Open app");
        const BUTTON_LABEL_ADD = _("Add to the desktop");
        const BUTTON_TOOLTIP_NO_NETWORK = _("No network connection is available");
        const BUTTON_TOOLTIP_NO_SPACE = _("Insufficient space to install the app");

        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                if (this.appInfo.get_has_launcher()) {
                    this._installButtonLabel.set_text(BUTTON_LABEL_LAUNCH);
                }
                else {
                    this._installButtonLabel.set_text(BUTTON_LABEL_ADD);
                }

                this._installButton.show();

                // Only apps that don't have a launcher can be
                // removed from the system
                if (!this.appInfo.get_has_launcher() && this.appInfo.is_removable()) {
                    this._removeButton.show();
                }
                break;

            case EosAppStorePrivate.AppState.AVAILABLE:
                this._installButton.set_tooltip_text("");
                this._installButtonLabel.set_text(BUTTON_LABEL_INSTALL);

                if (!this.model.networkAvailable) {
                    this._installButton.set_sensitive(false);
                    this._installButton.set_tooltip_text(BUTTON_TOOLTIP_NO_NETWORK);
                }
                else if (!this.appInfo.check_install_space()) {
                    this._installButton.set_sensitive(false);
                    this._installButton.set_tooltip_text(BUTTON_TOOLTIP_NO_SPACE);
                }
                else {
                    this._installButton.set_sensitive(true);
                }

                this._installButton.show();

                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                if (this.appInfo.get_has_launcher()) {
                    this._installButton.set_sensitive(this.model.networkAvailable);
                    if (!this.model.networkAvailable)
                        this._installButton.set_tooltip_text(BUTTON_TOOLTIP_NO_NETWORK);

                    this._installButtonLabel.set_text(BUTTON_LABEL_UPDATE);
                }
                else {
                    this._installButtonLabel.set_text(BUTTON_LABEL_ADD);
                    // like the .INSTALLED case, we only show the 'delete app'
                    // button if the app does not have a launcher on the desktop
                    this._removeButton.show();
                }
                this._installButton.show();
                break;

            case EosAppStorePrivate.AppState.UNKNOWN:
                log('The state of app "' + this.appId + '" is not known to the app store');
                break;
        }

        this._syncTransactionState();
    },

    _syncTransactionState: function() {
        let hasLauncher = this.appInfo.get_has_launcher();
        let isInstalling = this.appInfo.is_installing();
        let isUpdating = this.appInfo.is_updating();
        let isRemoving = this.appInfo.is_removing();

        if (isInstalling || isRemoving || isUpdating) {
            this._installButton.hide();
            this._removeButton.hide();

            // show the box with the progress bar and the label
            this._installProgress.show();

            // conditionally show the progress bar and cancel button
            if (isUpdating || isInstalling) {
                if (isInstalling && hasLauncher) {
                    this._installProgressLabel.set_text(_("Installing…"));
                }
                else {
                    this._installProgressLabel.set_text(_("Downloading…"));
                }

                this._installProgressSpinner.show();
                this._installProgressSpinner.start();
                this._installProgressCancel.show();
            }
            else {
                this._installProgressLabel.set_text(_("Removing…"));
                this._installProgressBar.hide();
                this._installProgressSpinner.hide();
                this._installProgressCancel.hide();
            }
        }
        else {
            this._installProgress.hide();
        }
    },

    _launchApp: function() {
        try {
            this.model.launch(this.appId, Gtk.get_current_event_time());

            let appWindow = Gio.Application.get_default().mainWindow;
            if (appWindow && appWindow.is_visible()) {
                appWindow.hide();
            }
        } catch (e) {
            log("Failed to launch app '" + this.appId + "': " + e.message);
        }
    },

    _onInstallButtonClicked: function() {
        switch (this._appState) {
            // if the application is installed, we have two options
            case EosAppStorePrivate.AppState.INSTALLED:
                // we launch it, if we have a launcher on the desktop
                if (this.appInfo.get_has_launcher()) {
                    this._launchApp();
                }
                // or we add a launcher on the desktop
                else {
                    this.doInstall();
                }
                break;

            // if the application is uninstalled, we install it
            case EosAppStorePrivate.AppState.AVAILABLE:
                this.doInstall();
                break;

            // if the application can be updated, we have two options
            case EosAppStorePrivate.AppState.UPDATABLE:
                // we update it, if we have a launcher on the desktop
                if (this.appInfo.get_has_launcher()) {
                    this.doUpdate();
                }
                // or we add a launcher on the desktop
                else {
                    this._addToDesktop();
                }
                break;
        }
    },

    _onInstallCancelButtonClicked: function() {
        this.doCancel();
    },

    _onRemoveButtonClicked: function() {
        let responseId = this.showRemoveDialog();

        if (responseId == Gtk.ResponseType.APPLY) {
            this.doRemove();
        }
    },
});
Builder.bindTemplateChildren(AppInfoBox.prototype);
