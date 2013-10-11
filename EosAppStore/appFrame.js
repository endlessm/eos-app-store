// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Mainloop = imports.mainloop;
const PLib = imports.gi.PLib;
const Endless = imports.gi.Endless;

const AppListModel = imports.appListModel;
const CategoryButton = imports.categoryButton;
const Builder = imports.builder;
const Lang = imports.lang;
const Separator = imports.separator;
const Signals = imports.signals;

const APP_TRANSITION_MS = 500;
const CATEGORY_TRANSITION_MS = 500;

const CELL_DEFAULT_SIZE = 180;
const CATEGORIES_BOX_SPACING = 32;
const STACK_TOP_MARGIN = 4;

const SCREENSHOT_LARGE = 480;
const SCREENSHOT_SMALL = 120;

// If the area available for the grid is less than this minimium size,
// scroll bars will be added.
const MIN_GRID_WIDTH = 800;
const MIN_GRID_HEIGHT = 600;

const AppPreview = new Lang.Class({
    Name: 'AppPreviewImage',
    Extends: Gtk.EventBox,

    _init: function(path) {
        this.parent();

        this._path = path;

        this._image = new Gtk.Image();
        this.add(this._image);

        EosAppStorePrivate.app_load_screenshot(this._image, this._path, SCREENSHOT_SMALL);
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
        '_installButtonLabel',
        '_installProgress',
        '_installProgressLabel',
        '_installSpinner',
        '_installedMessage',
        '_removeButton',
        '_removeButtonLabel',
        '_screenshotImage',
        '_screenshotPreviewBox',
    ],

    _init: function(model, appInfo) {
        this.parent();

        this._model = model;
        this._model.connect('changed', Lang.bind(this, this._updateState));
        this._appId = appInfo.get_desktop_id();

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);

        let separator = new Separator.FrameSeparator();
        this._mainBox.add(separator);
        this._mainBox.reorder_child(separator, 0);

        this._mainBox.show();

        this.appInfo = appInfo;
        this.appDescription = this.appInfo.get_description();
        this.appScreenshots = this.appInfo.get_screenshots();
        this._updateState();
    },

    _updateState: function() {
        this.appState = this._model.getState(this._appId);
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
                EosAppStorePrivate.app_load_screenshot(this._screenshotImage, path, SCREENSHOT_LARGE);
            }

            let previewBox = new AppPreview(path);
            this._screenshotPreviewBox.add(previewBox);
            previewBox.connect('button-press-event', Lang.bind(this, this._onPreviewPress));
            previewBox.show();

            this._screenshotPreviewBox.show();
        }
    },

    _onPreviewPress: function(widget, event) {
        EosAppStorePrivate.app_load_screenshot(this._screenshotImage, widget.path, SCREENSHOT_LARGE);
        return false;
    },

    _setStyleClassFromState: function() {
        let classes = [ { state: EosAppStorePrivate.AppState.UNINSTALLED,
                          style: 'install' },
                        { state: EosAppStorePrivate.AppState.UPDATABLE,
                          style: 'update' } ];

        let context = this._installButton.get_style_context();

        for (let idx in classes) {
            let obj = classes[idx];
            let state = obj.state;
            let styleClass = obj.style;

            if (state == this._appState) {
                context.add_class(styleClass);
            } else {
                context.remove_class(styleClass);
            }
        }
    },

    set appState(state) {
        this._appState = state;

        this._setStyleClassFromState();

        this._installButton.hide();
        this._removeButton.hide();

        switch (this._appState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                if (!this._installedMessage.visible) {
                    // wait for the message to hide
                    this._removeButton.show();
                }
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._installButtonLabel.set_text(_("Install application"));
                this._installButton.show();
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                this._installButtonLabel.set_text(_("Update application"));
                this._installButton.show();
                this._removeButton.show();
                break;

            case EosAppStorePrivate.AppState.UNKNOWN:
                log('The state of app "' + this._appId + '" is not known to the app store');
                break;
        }
    },

    _onInstallButtonClicked: function() {
        switch (this._appState) {
            case EosAppStorePrivate.AppState.UNINSTALLED:

                this._installButton.hide();
                this._installProgress.show();
                this._installSpinner.start();

                this._model.install(this._appId, Lang.bind(this, function(model, res) {
                    this._installProgress.hide();

                    try {
                        model.install_app_finish(res);
                        this._installedMessage.show();

                        Mainloop.timeout_add_seconds(3, Lang.bind(this, function() {
                            this._installedMessage.hide();
                            this._updateState();
                            return false;
                        }));
                    } catch (e) {
                        log('Failed to install app ' + e.message);
                        this._updateState();
                    }
                }));
                break;

            case EosAppStorePrivate.AppState.UPDATABLE:
                this._model.updateApp(this._appId);
                break;
        }
    },

    _onRemoveButtonClicked: function() {
        this._model.uninstall(this._appId, Lang.bind(this, function(model, res) {
            try {
                model.uninstall_app_finish(res);
            } catch (e) {
                log('Failed to uninstall app ' + e.message);
            }
        }));
    },
});
Builder.bindTemplateChildren(AppListBoxRow.prototype);

const AppFrame = new Lang.Class({
    Name: 'AppFrame',
    Extends: Gtk.Frame,

    _init: function() {
        this.parent();

        this.get_style_context().add_class('app-frame');

        this._categories = [
            {
                name: 'featured',
                widget: null,
                label: _("Featured"),
                id: EosAppStorePrivate.AppCategory.FEATURED,
            },
            {
                name: 'education',
                widget: null,
                label: _("Education"),
                id: EosAppStorePrivate.AppCategory.EDUCATION,
            },
            {
                name: 'leisure',
                widget: null,
                label: _("Leisure"),
                id: EosAppStorePrivate.AppCategory.LEISURE,
            },
            {
                name: 'utilities',
                widget: null,
                label: _("Utilities"),
                id: EosAppStorePrivate.AppCategory.UTILITIES,
            },
            {
                name: 'my-applications',
                widget: null,
                label: _("My applications"),
                id: EosAppStorePrivate.AppCategory.MY_APPLICATIONS,
            },
        ];

        this._backClickedId = 0;

        this._currentCategory = this._categories[0].name;
        this._currentCategoryIdx = 0;

        // initialize the applications model
        this._model = new AppListModel.AppList();

        this._mainStack = new PLib.Stack({ transition_duration: APP_TRANSITION_MS,
                                           transition_type: PLib.StackTransitionType.SLIDE_RIGHT,
                                           hexpand: true,
                                           vexpand: true });
        this.add(this._mainStack);
        this._mainStack.show();

        this._mainBox = new Gtk.Box({ orientation: Gtk.Orientation.VERTICAL,
                                      hexpand: true,
                                      vexpand: true });
        this._mainStack.add_named(this._mainBox, 'main-box');
        this._mainBox.show();

        this._categoriesBox = new Gtk.Box({ orientation: Gtk.Orientation.HORIZONTAL,
                                            spacing: CATEGORIES_BOX_SPACING,
                                            hexpand: true });
        this._mainBox.add(this._categoriesBox);
        this._categoriesBox.show();

        let separator = new Separator.FrameSeparator();
        this._mainBox.add(separator);

        this._stack = new PLib.Stack({ transition_duration: CATEGORY_TRANSITION_MS,
                                       transition_type: PLib.StackTransitionType.SLIDE_RIGHT,
                                       hexpand: true,
                                       vexpand: true,
                                       margin_top: STACK_TOP_MARGIN });
        this._mainBox.add(this._stack);
        this._stack.show();

        this._buttonGroup = null;
        this._model.connect('changed', Lang.bind(this, this._populateCategories));
        this._populateCategories();

        let content_dir = EosAppStorePrivate.app_get_content_dir();
        let content_path = GLib.build_filenamev([content_dir, 'content.json']);
        let content_file = Gio.File.new_for_path(content_path);
        this._contentMonitor = content_file.monitor_file(Gio.FileMonitorFlags.NONE, null);
        this._contentMonitor.connect('changed', Lang.bind(this, this._onContentChanged));

        this._stack.set_visible_child_name(this._currentCategory);
    },

    _onContentChanged: function(monitor, file, other_file, event_type) {
        this._populateCategories();
        this._stack.set_visible_child_name(this._currentCategory);
    },

    _populateCategories: function() {
        let cellStyle = EosAppStorePrivate.AppInfo.get_cell_style_context();
        let margin = cellStyle.get_margin(Gtk.StateFlags.NORMAL);
        let cellMargin = Math.max(margin.top, margin.right, margin.bottom, margin.left);

        for (let c in this._categories) {
            let category = this._categories[c];

            if (!category.button) {
                category.button = new CategoryButton.CategoryButton({ label: category.label,
                                                                      category: category.name,
                                                                      index: c,
                                                                      draw_indicator: false,
                                                                      group: this._buttonGroup });
                category.button.connect('clicked', Lang.bind(this, this._onCategoryClicked));
                category.button.show();
                this._categoriesBox.pack_start(category.button, false, false, 0);

                if (!this._buttonGroup) {
                    this._buttonGroup = category.button;
                }
            }

            let scrollWindow;

            if (!category.widget) {
                scrollWindow = new Gtk.ScrolledWindow({ hscrollbar_policy: Gtk.PolicyType.NEVER,
                                                        vscrollbar_policy: Gtk.PolicyType.AUTOMATIC });
                this._stack.add_named(scrollWindow, category.name);
                category.widget = scrollWindow;
            } else {
                scrollWindow = category.widget;
                let child = scrollWindow.get_child();
                child.destroy();
            }

            let grid = new Endless.FlexyGrid({ cell_size: CELL_DEFAULT_SIZE + cellMargin });
            scrollWindow.add_with_viewport(grid);

            let appInfos = EosAppStorePrivate.app_load_content(category.id);
            if (category.id == EosAppStorePrivate.AppCategory.MY_APPLICATIONS) {
                let installedApps = this._model.apps;

                for (let i in appInfos) {
                    let id = appInfos[i].get_desktop_id() + '.desktop';

                    let isInstalled = false;
                    for (let j in installedApps) {
                        if (installedApps[j] == id &&
                            this._model.getState(id) == EosAppStorePrivate.AppState.INSTALLED) {
                            isInstalled = true;
                            break;
                        }
                    }

                    if (isInstalled) {
                        let cell = appInfos[i].create_cell();
                        cell.shape = Endless.FlexyShape.SMALL;
                        grid.add(cell);
                        cell.show_all();
                    }
                }
            }
            else {
                for (let i in appInfos) {
                    let cell = appInfos[i].create_cell();
                    grid.add(cell);
                    cell.show_all();
                }
            }

            grid.connect('cell-activated', Lang.bind(this, this._onCellActivated));

            scrollWindow.show_all();
        }
    },

    _onCellActivated: function(grid, cell) {
        let appBox = new AppListBoxRow(this._model, cell.app_info);
        appBox.show();

        this._mainStack.add_named(appBox, cell.desktop_id);
        this._mainStack.transition_type = PLib.StackTransitionType.SLIDE_LEFT;
        this._mainStack.set_visible_child_name(cell.desktop_id);

        let app = Gio.Application.get_default();
        app.mainWindow.titleText = cell.app_info.get_title();
        app.mainWindow.subtitleText = cell.app_info.get_subtitle();
        app.mainWindow.headerIcon = this._model.getIcon(cell.desktop_id);

        let appState = this._model.getState(cell.desktop_id);
        app.mainWindow.headerInstalledVisible = (appState == EosAppStorePrivate.AppState.INSTALLED);
        app.mainWindow.backButtonVisible = true;
        this._backClickedId =
            app.mainWindow.connect('back-clicked', Lang.bind(this, this._showGrid));
    },

    _showGrid: function() {
        let app = Gio.Application.get_default();
        app.mainWindow.titleText = null;
        app.mainWindow.subtitleText = null;
        app.mainWindow.headerIcon = null;
        app.mainWindow.headerInstalledVisible = false;
        app.mainWindow.backButtonVisible = false;

        if (this._backClickedId > 0) {
            app.mainWindow.disconnect(this._backClickedId);
            this._backClickedId = 0;
        }

        let curPage = this._mainStack.get_visible_child();
        this._mainStack.transition_type = PLib.StackTransitionType.SLIDE_RIGHT;
        this._mainStack.set_visible_child_name('main-box');

        if (curPage != this._mainBox) {
            // application pages are recreated each time
            curPage.destroy();
        }
    },

    _onCategoryClicked: function(button) {
        let category = button.category;
        let idx = button.index;

        // Scroll to the top of the selected category
        let widget = this._categories[idx].widget;
        if (widget) {
            let vscrollbar = widget.get_vscrollbar();
            vscrollbar.set_value(0);
        }

        if (idx > this._currentCategoryIdx) {
            this._stack.transition_type = PLib.StackTransitionType.SLIDE_LEFT;
        } else {
            this._stack.transition_type = PLib.StackTransitionType.SLIDE_RIGHT;
        }

        this._currentCategory = category;
        this._currentCategoryIdx = idx;

        this._stack.set_visible_child_name(category);
    },

    reset: function() {
        // Return to the first category
        this._showGrid();
        this._buttonGroup.clicked();
    }
});
