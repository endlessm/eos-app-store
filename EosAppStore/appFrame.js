// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Mainloop = imports.mainloop;
const Endless = imports.gi.Endless;

const AppListModel = imports.appListModel;
const AppStoreWindow = imports.appStoreWindow;
const Builder = imports.builder;
const Categories = imports.categories;
const CategoryButton = imports.categoryButton;
const Lang = imports.lang;
const Notify = imports.notify;
const Separator = imports.separator;
const Signals = imports.signals;

const APP_TRANSITION_MS = 500;
const CATEGORY_TRANSITION_MS = 500;
const SHOW_DESKTOP_ICON_DELAY = 1;

const CELL_DEFAULT_SIZE = 180;
const CELL_DEFAULT_SPACING = 15;
const CATEGORIES_BOX_SPACING = 32;
const STACK_TOP_MARGIN = 4;

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

const AppListBoxRow = new Lang.Class({
    Name: 'AppListBoxRow',
    Extends: Gtk.Bin,

    templateResource: '/com/endlessm/appstore/eos-app-store-list-row.ui',
    templateChildren: [
        '_mainBox',
        '_contentBox',
        '_descriptionText',
        '_installButton',
        '_installButtonImage',
        '_installButtonLabel',
        '_installProgress',
        '_installProgressLabel',
        '_installProgressBar',
        '_installProgressCancel',
        '_installedMessage',
        '_removeButton',
        '_removeButtonImage',
        '_removeButtonLabel',
        '_screenshotImage',
        '_screenshotPreviewBox',
    ],

    _init: function(model, appInfo) {
        this.parent();

        let app = Gio.Application.get_default();
        let mainWindow = app.mainWindow;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);

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

        this.appInfo = appInfo;
        this.appTitle = this.appInfo.get_title();
        this.appDescription = this.appInfo.get_description();
        this.appScreenshots = this.appInfo.get_screenshots();
        this._appId = appInfo.get_desktop_id();

        this._model = model;
        this._changedId = this._model.connect('changed', Lang.bind(this, this._updateState));
        this._progressId = this._model.connect('download-progress', Lang.bind(this, this._downloadProgress));

        this._removeDialog = null;
        this._windowHideId = mainWindow.connect('hide', Lang.bind(this, this._destroyPendingDialogs));
        this.connect('destroy', Lang.bind(this, this._onDestroy));

        this._installButton.connect('state-flags-changed', Lang.bind(this, this._onInstallButtonStateChanged));
        this._removeButton.connect('state-flags-changed', Lang.bind(this, this._onRemoveButtonStateChanged));

        let separator = new Separator.FrameSeparator();
        this._mainBox.add(separator);
        this._mainBox.reorder_child(separator, 0);
        this._mainBox.show();

        this._updateState();
    },

    _destroyRemoveDialog: function() {
        if (this._removeDialog != null) {
            this._removeDialog.destroy();
            this._removeDialog = null;
        }
    },

    _destroyErrorDialog: function() {
        if (this._errorDialog != null) {
            this._errorDialog.destroy();
            this._errorDialog = null;
        }
    },

    _destroyPendingDialogs: function() {
        this._destroyRemoveDialog();
        this._destroyErrorDialog();
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

        if (this._changedId != 0) {
            this._model.disconnect(this._changedId);
            this._changedId = 0;
        }

        if (this._progressId != 0) {
            this._model.disconnect(this._progressId);
            this._progressId = 0;
        }
    },

    _updateState: function() {
        this.appState = this._model.getState(this._appId);
    },

    _downloadProgress: function(model, appid, progress, current, total) {
        if (this.appId != appid) {
            return;
        }

        if (current == 0) {
            this._installProgressLabel.set_text(_("Downloading…"));
            this._installProgressBar.fraction = 0.0;
            return;
        }

        if (current == total) {
            this._installProgressLabel.set_text(_("Installing…"));
            this._installProgressBar.fraction = 1.0;
            return;
        }

        this._installProgressBar.fraction = progress;
    },

    get hasTransactionInProgress() {
        return this._transactionInProgress;
    },

    get appId() {
        return this._appId;
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

        for (let i in screenshots) {
            let path = screenshots[i];

            if (i == 0) {
                EosAppStorePrivate.app_load_screenshot(this._screenshotImage, path, this._screenshotLarge);
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

    _onRemoveButtonStateChanged: function() {
        // We use the background-image of a GtkFrame to set the image,
        // and we need to forward the state flags to it, since GtkFrame
        // can't track hover/active alone
        let stateFlags = this._removeButton.get_state_flags();
        this._removeButtonImage.set_state_flags(stateFlags, true);
    },

    _onInstallButtonStateChanged: function() {
        // We use the background-image of a GtkFrame to set the image,
        // and we need to forward the state flags to it, since GtkFrame
        // can't track hover/active alone
        let stateFlags = this._installButton.get_state_flags();
        this._installButtonImage.set_state_flags(stateFlags, true);
    },

    _setStyleClassFromState: function() {
        const INSTALL = 0;
        const UPDATE = 1;
        const ADD = 2;
        const LAUNCH = 3;
        let style = INSTALL;

        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                if (this._model.hasLauncher(this._appId)) {
                    style = LAUNCH;
                }
                else {
                    style = ADD;
                }
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                style = INSTALL;
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                if (this._model.hasLauncher(this._appId)) {
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

        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                // wait for the message to hide
                if (!this._installedMessage.visible) {
                    if (this._model.hasLauncher(this._appId)) {
                        this._installButtonLabel.set_text(BUTTON_LABEL_LAUNCH);
                    }
                    else {
                        this._installButtonLabel.set_text(BUTTON_LABEL_ADD);
                    }

                    this._installButton.show();

                    if (this._model.canRemove(this._appId)) {
                        this._removeButton.show();
                    }
                }
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._installButtonLabel.set_text(BUTTON_LABEL_INSTALL);
                this._installButton.show();
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                if (this._model.hasLauncher(this._appId)) {
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
                log('The state of app "' + this._appId + '" is not known to the app store');
                break;
        }

        // force buttons to be hidden if there's a transaction
        // in progress; we still want the various checks above
        // to happen regardless
        if (this.hasTransactionInProgress) {
            this._installButton.hide();
            this._removeButton.hide();
        }
    },

    _pushTransaction: function(text, showProgressBar) {
        this._transactionInProgress = true;

        // hide install/remove buttons
        this._installButton.hide();
        this._removeButton.hide();

        // show the box with the progress bar and the label
        this._installProgress.show();

        // show the label
        this._installProgressLabel.set_text(text);

        // conditionally show the progress bar and cancel button
        if (showProgressBar) {
            this._installProgressBar.fraction = 0.0;
            this._installProgressBar.show();
            this._installProgressCancel.show();
        }
        else {
            this._installProgressBar.hide();
            this._installProgressCancel.hide();
        }

        let app = Gio.Application.get_default();
        app.pushRunningOperation();
    },

    _popTransaction: function() {
        this._transactionInProgress = false;

        this._installProgress.hide();

        let app = Gio.Application.get_default();
        app.popRunningOperation();
    },

    _installOrAddToDesktop: function() {
        this._model.install(this._appId, Lang.bind(this, function(error) {
            this._popTransaction();

            if (error) {
                this._maybeNotify(_("We could not install '%s'").format(this.appTitle), error);
                this._updateState();
                return;
            }

            this._maybeNotify(_("'%s' was installed successfully").format(this.appTitle));

            this._installedMessage.show();
            Mainloop.timeout_add_seconds(SHOW_DESKTOP_ICON_DELAY,
                                         Lang.bind(this, function() {
                this._installedMessage.hide();
                this._updateState();

                let appWindow = Gio.Application.get_default().mainWindow;
                if (appWindow && appWindow.is_visible()) {
                    appWindow.hide();
                }

                return false;
            }));
        }));
    },

    _installApp: function() {
        this._pushTransaction(_("Downloading…"), true);
        this._installOrAddToDesktop();
    },

    _updateApp: function() {
        this._pushTransaction(_("Updating…"), true);

        this._model.updateApp(this._appId, Lang.bind(this, function(error) {
            this._popTransaction();
            this._updateState();

            if (error) {
                this._maybeNotify(_("We could not update '%s'").format(this.appTitle), error);
            }
            else {
                    this._maybeNotify(_("'%s' was updated successfully").format(this.appTitle));
            }
        }));
    },

    _launchApp: function() {
        try {
            this._model.launch(this._appId, Gtk.get_current_event_time());

            let appWindow = Gio.Application.get_default().mainWindow;
            if (appWindow && appWindow.is_visible()) {
                appWindow.hide();
            }
        } catch (e) {
            log("Failed to launch app '" + this._appId + "': " + e.message);
        }
    },

    _addToDesktop: function() {
        this._pushTransaction(_("Installing…"), false);
        this._installOrAddToDesktop();
    },

    _onInstallButtonClicked: function() {
        switch (this._appState) {
            // if the application is installed, we have two options
            case EosAppStorePrivate.AppState.INSTALLED:
                // we launch it, if we have a launcher on the desktop
                if (this._model.hasLauncher(this._appId)) {
                    this._launchApp();
                }
                // or we add a launcher on the desktop
                else {
                    this._addToDesktop();
                }
                break;

            // if the application is uninstalled, we install it
            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._installApp();
                break;

            // if the application can be updated, we have two options
            case EosAppStorePrivate.AppState.UPDATABLE:
                // we update it, if we have a launcher on the desktop
                if (this._model.hasLauncher(this._appId)) {
                    this._updateApp();
                }
                // or we add a launcher on the desktop
                else {
                    this._addToDesktop();
                }
                break;
        }
    },

    _onInstallCancelButtonClicked: function() {
        // this will trigger the error handling code in the install/update paths
        this._model.cancel(this._appId);
    },

    _onRemoveButtonClicked: function() {
        let app = Gio.Application.get_default();

        let dialog = new Gtk.MessageDialog();
        dialog.set_transient_for(app.mainWindow);
        dialog.modal = true;
        dialog.destroy_with_parent = true;
        dialog.text = _("Deleting app");
        dialog.secondary_text = _("Deleting this app will remove it from the device for all users. You will need to download it from the internet in order to reinstall it.");
        let applyButton = dialog.add_button(_("Delete app"), Gtk.ResponseType.APPLY);
        applyButton.get_style_context().add_class('destructive-action');
        dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL);
        dialog.show_all();
        this._removeDialog = dialog;

        let responseId = this._removeDialog.run();
        this._destroyRemoveDialog();

        if (responseId == Gtk.ResponseType.APPLY) {
            this._pushTransaction(_("Removing…"), false);

            this._model.uninstall(this._appId, Lang.bind(this, function(error) {
                this._popTransaction();

                if (error) {
                    this._maybeNotify(_("We could not remove '%s'").format(this.appTitle), error);
                }
                else {
                    this._maybeNotify(_("'%s' was removed successfully").format(this.appTitle));
                }

                this._updateState();
            }));
        }
    },

    _maybeNotify: function(message, error) {
        let app = Gio.Application.get_default();
        let appWindowVisible = false;
        if (app.mainWindow) {
            appWindowVisible = app.mainWindow.is_visible();
        }
        else {
            // the app store window timeout triggered, but the
            // app store process is still running because of the
            // reference we hold
            appWindowVisible = false;
        }

        // notify only if the error is not caused by a user
        // cancellation
        if (error &&
            (error.matches(Gio.io_error_quark(),
                           Gio.IOErrorEnum.CANCELLED) ||
             error.matches(EosAppStorePrivate.AppListModel.error_quark(),
                           EosAppStorePrivate.AppListModelError.CANCELLED))) {
            return;
        }

        // if the window is not visible, we emit a notification instead
        // of showing a dialog
        if (!appWindowVisible) {
            let notification = new Notify.Notification(message, '');
            notification.show();
            return;
        }

        // we only show the error dialog if the error is set
        if (error) {
            let dialog = new Gtk.MessageDialog();
            dialog.set_transient_for(app.mainWindow);
            dialog.modal = true;
            dialog.destroy_with_parent = true;
            dialog.text = message;
            dialog.secondary_text = error.message;
            dialog.add_button(_("Dismiss"), Gtk.ResponseType.OK);
            dialog.show_all();
            this._errorDialog = dialog;
            this._errorDialog.run();
            this._destroyErrorDialog();
        }
    },
});
Builder.bindTemplateChildren(AppListBoxRow.prototype);

const AppCategoryFrame = new Lang.Class({
    Name: 'AppCategoryFrame',
    Extends: Gtk.Frame,

    _init: function(category, model, mainWindow) {
        this.parent();

        this.get_style_context().add_class('app-frame');

        this._stack = new Gtk.Stack({ transition_duration: APP_TRANSITION_MS,
                                      transition_type: Gtk.StackTransitionType.SLIDE_RIGHT,
                                      hexpand: true,
                                      vexpand: true });
        this.add(this._stack);

        this._category = category;
        this._mainWindow = mainWindow;
        this._model = model;

        this._backClickedId = 0;
        this._lastCellSelected = null;
        this._widget = null;

        let box = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL,
                                hexpand: true,
                                vexpand: true });
        this._stack.add_named(box, 'spinner');
        box.show();
        
        box.add(new Separator.FrameSeparator());

        this._spinner = new Gtk.Spinner({ halign: Gtk.Align.CENTER,
                                          valign: Gtk.Align.CENTER,
                                          hexpand: true,
                                          vexpand: true });
        box.add(this._spinner);

        this.show_all();

        this._stack.set_visible_child_full('spinner', Gtk.StackTransitionType.CROSSFADE);
        this._spinner.start();
    },

    invalidate: function() {
        if (this._widget) {
            this._widget.destroy();
            this._widget = null;
        }

        this._stack.set_visible_child_full('spinner', Gtk.StackTransitionType.CROSSFADE);
        this._spinner.start();
    },

    populate: function() {
        if (this._widget) {
            return;
        }

        if (this._model.isRefreshing) {
            return;
        }

        let box = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL,
                                hexpand: true,
                                vexpand: true });
        this._stack.add_named(box, 'app-frame');
        this._widget = box;

        let separator = new Separator.FrameSeparator();
        box.add(separator);

        let scrollWindow = new Gtk.ScrolledWindow({ hscrollbar_policy: Gtk.PolicyType.NEVER,
                                                    vscrollbar_policy: Gtk.PolicyType.AUTOMATIC });
        box.add(scrollWindow);

        let cellMargin = EosAppStorePrivate.AppInfo.get_cell_margin();
        let grid = new Endless.FlexyGrid({ cell_size: CELL_DEFAULT_SIZE + cellMargin,
                                           cell_spacing: CELL_DEFAULT_SPACING - cellMargin });
        scrollWindow.add_with_viewport(grid);

        let appInfos = EosAppStorePrivate.app_load_content(this._category.id,
                                                           Lang.bind(this, function(appInfo) {
            let id = appInfo.get_desktop_id();
            return this._model.hasApp(id);
        }));

        if (this._category.id == EosAppStorePrivate.AppCategory.INSTALLED) {
            // 'Installed' only shows apps available on the desktop...
            for (let i in appInfos) {
                let id = appInfos[i].get_desktop_id();

                if (this._model.hasLauncher(id)) {
                    let cell = appInfos[i].create_cell(this._model.getIcon(id));
                    cell.shape = Endless.FlexyShape.SMALL;
                    grid.add(cell);
                }
            }
        }
        else {
            // ... while every other category only shows apps that can be added
            for (let i in appInfos) {
                let id = appInfos[i].get_desktop_id();

                if (!this._model.hasLauncher(id)) {
                    let cell = appInfos[i].create_cell(this._model.getIcon(id));
                    grid.add(cell);
                }
            }
        }

        grid.connect('cell-selected', Lang.bind(this, this._onCellSelected));
        grid.connect('cell-activated', Lang.bind(this, this._onCellActivated));

        box.show_all();

        this._stack.set_visible_child_full('app-frame', Gtk.StackTransitionType.CROSSFADE);
        this._spinner.stop();
    },

    _onCellSelected: function(grid, cell) {
        if (this._lastCellSelected != cell) {
            if (this._lastCellSelected) {
                this._lastCellSelected.selected = false;
            }

            this._lastCellSelected = cell;

            if (this._lastCellSelected) {
                this._lastCellSelected.selected = true;
            }
        }
    },

    _onCellActivated: function(grid, cell) {
        if (!this._stack.get_child_by_name(cell.desktop_id)) {
            let appBox = new AppListBoxRow(this._model, cell.app_info);
            appBox.show();

            this._stack.add_named(appBox, cell.desktop_id);
            this._stack.transition_type = Gtk.StackTransitionType.SLIDE_LEFT;
        }

        this._stack.set_visible_child_name(cell.desktop_id);

        this._mainWindow.titleText = cell.app_info.get_title();
        this._mainWindow.subtitleText = cell.app_info.get_subtitle();
        this._mainWindow.headerIcon = this._model.getIcon(cell.desktop_id);
        this._mainWindow.headerInstalledVisible = this._model.isInstalled(cell.desktop_id);
        this._mainWindow.backButtonVisible = true;

        this._backClickedId =
            this._mainWindow.connect('back-clicked', Lang.bind(this, this._showGrid));
    },

    _showGrid: function() {
        let curPage = this._stack.get_visible_child();
        this._mainWindow.clearHeaderState();

        if (this._backClickedId > 0) {
            this._mainWindow.disconnect(this._backClickedId);
            this._backClickedId = 0;
        }

        if (this._widget) {
            this._stack.transition_type = Gtk.StackTransitionType.SLIDE_RIGHT;
            this._stack.set_visible_child(this._widget);
        }

        // application pages are recreated each time, unless there's
        // a transaction in progress
        let curPageName = this._stack.visible_child_name;
        if (!(curPageName == 'app-frame' || curPageName == 'spinner') &&
            !curPage.hasTransactionInProgress) {
            curPage.destroy();
        }
    },

    reset: function() {
        if (this._model.isRefreshing) {
            if (this._stack.visible_child_name != 'spinner') {
                this._stack.set_visible_child_full('spinner', Gtk.StackTransitionType.CROSSFADE);
            }
            return;
        }

        this._showGrid();
        this.populate();
    },

    get title() {
        return _("Install apps");
    }
});

const AppBroker = new Lang.Class({
    Name: 'AppBroker',

    _init: function(mainWindow) {
        this._mainWindow = mainWindow;

        // initialize the applications model
        this._model = new AppListModel.AppList();
        this._model.refresh(Lang.bind(this, this._populateAllCategories));
        this._model.connect('changed', Lang.bind(this, this._populateAllCategories));

        this._categories = Categories.get_app_categories();
        this._categories.forEach(Lang.bind(this, function(category) {
            category.widget = new AppCategoryFrame(category, this._model, mainWindow);
        }));

        let content_dir = EosAppStorePrivate.app_get_content_dir();
        let content_path = GLib.build_filenamev([content_dir, 'content.json']);
        let content_file = Gio.File.new_for_path(content_path);
        this._contentMonitor = content_file.monitor_file(Gio.FileMonitorFlags.NONE, null);
        this._contentMonitor.connect('changed', Lang.bind(this, this._onContentChanged));
    },

    _onContentChanged: function(monitor, file, other_file, event_type) {
        this._populateAllCategories();
    },

    _populateAllCategories: function() {
        this._categories.forEach(Lang.bind(this, function(c) {
            c.widget.invalidate();
            c.widget.populate();
        }));
    },

    get categories() {
        return this._categories;
    }
});
