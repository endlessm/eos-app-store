// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Pango = imports.gi.Pango;
const WebKit = imports.gi.WebKit2;

const AppListModel = imports.appListModel;
const AppStoreWindow = imports.appStoreWindow;
const Categories = imports.categories;
const CategoryButton = imports.categoryButton;
const Builder = imports.builder;
const Lang = imports.lang;
const Path = imports.path;
const Separator = imports.separator;
const Signals = imports.signals;

const NEW_SITE_SUCCESS_TIMEOUT = 3;

const CATEGORY_TRANSITION_MS = 500;

const LIST_COLUMNS_SPACING = 10;

const DEFAULT_ICON = 'generic-link';
const EOS_BROWSER = 'chromium-browser ';
const DESKTOP_KEY_SPLASH = 'X-Endless-Splash-Screen';

const ICON_EXTERNAL_LINK = '/com/endlessm/appstore/icon_external-link.png';
const ICON_BLANK = '/com/endlessm/appstore/icon_blank.png';

function getAvailableFilename(path, prefix, name, suffix) {
    let filename = prefix + name;

    // Append a number until we find a free slot
    let availableFilename = filename + suffix;
    let availablePath = GLib.build_filenamev([path, availableFilename]);
    let i = 0;

    while (GLib.file_test(availablePath, GLib.FileTest.EXISTS)) {
        i++;
        availableFilename = filename + '-' + i + suffix;
        availablePath = GLib.build_filenamev([path, availableFilename]);
    }

    return [availableFilename, availablePath];
};

// FIXME: this should use the linkId as provided by the CMS.
// See https://github.com/endlessm/eos-shell/issues/1074
function createWeblink(url, title, icon) {
    let desktop = new GLib.KeyFile();

    // Let's compute a filename
    let filename = url;

    // Skip scheme
    let scheme = GLib.uri_parse_scheme(filename);
    if (scheme) {
        filename = filename.substr((scheme+'://').length);
    }

    // Get only the hostname part
    let tokens = filename.split('/');
    filename = tokens[0];

    // Get only domain name
    tokens = filename.split('.');
    if (tokens.length > 1) {
        filename = tokens[tokens.length-2];
    }

    let path = GLib.build_filenamev([GLib.get_user_data_dir(), 'applications']);
    GLib.mkdir_with_parents(path, parseInt('0755', 8));
    
    let [availableFilename, availablePath] = getAvailableFilename(path, 'eos-link-user-', filename, '.desktop');

    desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_VERSION, '1.0');
    desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_TYPE, 'Application');
    desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_EXEC, EOS_BROWSER + url);
    desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_ICON, icon);
    desktop.set_boolean(GLib.KEY_FILE_DESKTOP_GROUP, DESKTOP_KEY_SPLASH, false);
    desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_NAME, title);

    let [data, length] = desktop.to_data();
    GLib.file_set_contents(availablePath, data, length);

    return [availableFilename, availablePath, desktop];
};

const NewSiteHelper = new Lang.Class({
    Name: 'NewSiteHelper',

    _init: function(url) {
        this._url = url;
        this._title = null;

        this._favicon = null;
        this._faviconPath = null;

        this._savedKeyfile = null;
        this._savedKeyfilePath = null;

        this._webView = new WebKit.WebView();
        let context = this._webView.get_context();
        let cachePath = GLib.build_filenamev([GLib.get_user_cache_dir(),
                                              'eos-app-store', 'icondatabase']);
        context.set_favicon_database_directory(cachePath);

        this._webView.connect('load-failed', Lang.bind(this, this._onLoadFailed));
        this._webView.connect('notify::title', Lang.bind(this, this._onTitleLoaded));
        this._webView.connect('notify::favicon', Lang.bind(this, this._onFaviconLoaded));

        // check if the URL that the user entered already has a valid prefix
        if (url.indexOf('http://') != 0 && url.indexOf('https://') != 0 &&
            url.indexOf('ftp://')  != 0 && url.indexOf('file://')  != 0) {
            // if it does not start with a valid prefix, prepend http://
            url = 'http://' + url;
        }

        this._webView.load_uri(url);
    },

    _saveFavicon: function() {
        let path = GLib.build_filenamev([GLib.get_user_data_dir(), 'applications']);
        GLib.mkdir_with_parents(path, parseInt('0755', 8));

        let [iconFilename, iconPath] = getAvailableFilename(path, 'eos-link-', 'icon', '.png');
        EosAppStorePrivate.save_icon(this._favicon, 'png', iconPath);

        this._faviconPath = iconPath;
    },

    _updateFavicon: function() {
        this._savedKeyfile.set_string(GLib.KEY_FILE_DESKTOP_GROUP,
                                      GLib.KEY_FILE_DESKTOP_KEY_ICON,
                                      this._faviconPath);
        let [data, length] = this._savedKeyfile.to_data();
        GLib.file_set_contents(this._savedKeyfilePath, data, length);
    },

    _onFaviconLoaded: function() {
        let favicon = EosAppStorePrivate.link_get_favicon(this._webView);
        if (favicon) {
            this._favicon = favicon;
            this.emit('favicon-loaded');

            // if we saved the desktop file already, update it 
            // with the new icon
            if (this._savedKeyfile) {
                this._saveFavicon();
                this._updateFavicon();
            }
        }
    },

    _onTitleLoaded: function() {
        let title = this._webView.title;
        if (title) {
            this._title = title;
            this.emit('website-loaded');
        }
    },

    _onLoadFailed: function() {
        this.emit('website-failed');
    },

    get favicon() {
        return this._favicon;
    },

    get title() {
        return this._title;
    },

    get url() {
        return this._url;
    },

    save: function(title) {
        let icon = DEFAULT_ICON;

        // check if we already got a favicon
        if (this._favicon) {
            this._saveFavicon();
            icon = this._faviconPath;
        }

        let [desktopId, keyfilePath, keyfile] = createWeblink(this._url, title, icon);
        this._savedKeyfile = keyfile;
        this._savedKeyfilePath = keyfilePath;

        return desktopId;
    }
});
Signals.addSignalMethods(NewSiteHelper.prototype);

const NewSiteBoxState = {
    EMPTY: 0,
    READY: 1,
    SEARCHING: 2,
    FOUND: 3,
    ERROR: 4,
    INSTALLED: 5
};

const NewSiteBox = new Lang.Class({
    Name: 'NewSiteBox',
    Extends: Gtk.Bin,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-new-site-frame.ui',
    templateChildren: [
        '_mainBox',
        '_siteIcon',
        '_siteUrlFrame',
        '_siteAlertIconFrame',
        '_siteAlertLabelEventBox',
        '_siteAlertLabel',
        '_siteAddButton'
    ],

    _init: function(weblinkListModel) {
        this.parent();

        this._webHelper = null;
        this._weblinkListModel = weblinkListModel;

        this.initTemplate({ templateRoot: '_mainBox',
                            bindChildren: true,
                            connectSignals: true });
        this.add(this._mainBox);
        this._mainBox.show_all();

        this._alertIcons = [ null,
                             null,
                             new Gtk.Spinner({ name: 'spinner',
                                               width_request: 12,
                                               height_request: 12 }),
                             new Gtk.Button({ name: 'back',
                                              width_request: 22,
                                              height_request: 22 }),
                             new Gtk.Image({ name: 'alert',
                                             halign: Gtk.Align.CENTER,
                                             valign: Gtk.Align.CENTER }),
                             null ];

        this._alertIcons[NewSiteBoxState.FOUND].connect('clicked', Lang.bind(this, this._onFoundSiteBack));
        this._sitePixbuf = null;

        this._buildSearchBoxForNewSites();

        this._setState(NewSiteBoxState.EMPTY);
    },

    _buildSearchBoxForNewSites: function() {
        this._urlEntry = new Gtk.Entry({ margin_bottom: 12 });
        this._urlEntry.set_placeholder_text(_("Write the website you'd like to add here and press “Enter”"));
        this._urlEntry.get_style_context().add_class('url-entry');

        this._urlEntry.connect('enter-notify-event',
                               Lang.bind(this, function() {
                                   this._urlEntry.set_state_flags(Gtk.StateFlags.PRELIGHT, false);
                               }));

        this._urlEntry.connect('leave-notify-event',
                               Lang.bind(this, function() {
                                   this._urlEntry.unset_state_flags(Gtk.StateFlags.PRELIGHT);
                               }));

        this._urlEntry.connect('activate',
                               Lang.bind(this, this._onUrlEntryActivated));

        this._urlEntry.connect('changed',
                               Lang.bind(this, this._onUrlEntryChanged));

        this._urlEntry.connect('icon-press',
                               Lang.bind(this, function () {
                                   this._urlEntry.emit('activate');
                               }));

        this._urlLabel = new Gtk.Label();
        this._urlLabel.get_style_context().add_class('url-label');
        this._urlLabel.set_alignment(0, 0);
        this._urlLabel.show();

        this._siteAlertLabelEventBox.connect('enter-notify-event',
                                             Lang.bind(this, this._onSiteAlertEnterEvent));
        this._siteAlertLabelEventBox.connect('leave-notify-event',
                                             Lang.bind(this, this._onSiteAlertLeaveEvent));
        this._siteAlertLabelEventBox.connect('button-press-event',
                                             Lang.bind(this, this._onSiteAlertLabelClicked));

        this._siteUrlFrame.add(this._urlEntry);
    },

    _updateUrlFrameForState: function() {
        switch (this._state) {
        case NewSiteBoxState.EMPTY:
        case NewSiteBoxState.READY:
        case NewSiteBoxState.SEARCHING:
        case NewSiteBoxState.ERROR:
            if (this._siteUrlFrame.get_child() != this._urlEntry) {
                this._siteUrlFrame.remove(this._urlLabel);
                this._siteUrlFrame.add(this._urlEntry);
                this._urlEntry.show();
            }

            break;
        case NewSiteBoxState.FOUND:
        case NewSiteBoxState.INSTALLED:
            if (this._siteUrlFrame.get_child() != this._urlLabel) {
                this._siteUrlFrame.remove(this._urlEntry);
                this._siteUrlFrame.add(this._urlLabel);
                this._urlLabel.show();
            }

            break;
        }
    },

    _setState: function(state) {
        if (this._state == state) {
            return;
        }

        let prevState = this._state;
        this._state = state;
        this._switchAlertIcon(prevState);

        // Make sure this style is never applied by default when changing states.
        let eventBoxStyleContext = this._siteAlertLabelEventBox.get_style_context();
        if (eventBoxStyleContext.has_class('alert-highlight'))
            this._siteAlertLabelEventBox.get_style_context().remove_class('alert-highlight');

        // Prepare the frame where either the URL or the site title
        // will be shown, depending on the actual state.
        this._updateUrlFrameForState();

        switch (state) {
        case NewSiteBoxState.EMPTY:
            this._urlEntry.set_text('');
            this._urlEntry.grab_focus();
            // fall through
        case NewSiteBoxState.READY:
            this._siteAlertLabel.set_text(_("e.g.: http://www.prensalibre.com.gt"));

            this._siteAddButton.visible = false;
            this._urlEntry.max_length = 0;
            this._urlEntry.halign = Gtk.Align.FILL;
            this._sitePixbuf = null;

            // https://bugzilla.gnome.org/show_bug.cgi?id=709056
            let file = Gio.File.new_for_path(Path.ICONS_DIR + '/icon_website-symbolic.svg');
            let gicon = new Gio.FileIcon({ file: file });
            this._siteIcon.set_from_gicon(gicon, Gtk.IconSize.DND);

            if (this._webHelper) {
                this._webHelper.disconnectAll();
                this._webHelper = null;
            }

            break;
        case NewSiteBoxState.SEARCHING:
            this._siteAlertLabel.set_text(_("searching"));
            this._urlEntry.secondary_icon_name = null;
            this._urlEntry.get_style_context().remove_class('url-entry-error');

            break;
        case NewSiteBoxState.FOUND:
            this._urlLabel.set_label(this._webHelper.title);
            this._siteAlertLabel.set_text(this._webHelper.url);
            this._siteAddButton.visible = true;
            this._urlEntry.secondary_icon_name = null;

            break;
        case NewSiteBoxState.ERROR:
            this._siteAlertLabel.set_text(_("The address written does not exist or is not available."));
            this._urlEntry.secondary_icon_name = null;
            this._urlEntry.get_style_context().add_class('url-entry-error');

            break;
        case NewSiteBoxState.INSTALLED:
            this._siteAlertLabel.set_text(_("added successfully!"));
            this._urlLabel.set_label(this._webHelper.title);
            this._siteAddButton.sensitive = false;

            GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,
                                     NEW_SITE_SUCCESS_TIMEOUT,
                                     Lang.bind(this, function() {
                                         this._updateUrlFrameForState();
                                         this._siteAddButton.sensitive = true;
                                         this._setState(NewSiteBoxState.EMPTY);
                                         return false;
                                     }));
            break;
        }
    },

    _switchAlertIcon: function(prevState) {
        let oldAlertIcon = this._alertIcons[prevState];
        let alertIcon = this._alertIcons[this._state];

        if (oldAlertIcon) {
            this._siteAlertIconFrame.remove(oldAlertIcon);

            if (prevState == NewSiteBoxState.SEARCHING) {
                oldAlertIcon.stop();
            }
        }

        if (alertIcon) {
            this._siteAlertIconFrame.add(alertIcon);
            alertIcon.show();

            if (this._state == NewSiteBoxState.SEARCHING) {
                alertIcon.start();
            }
        }

        // We hide the icon frame only in the INSTALLED state, so that the
        // width request is not get the alert label misaligned in this case.
        this._siteAlertIconFrame.visible = (this._state != NewSiteBoxState.INSTALLED);
    },

    _onFoundSiteBack: function() {
        this._setState(NewSiteBoxState.EMPTY);
    },

    _onSiteAdd: function() {
        let title = this._urlEntry.get_text();

        let desktopId = this._webHelper.save(title);
        this._weblinkListModel.install(desktopId, function() {});

        this._setState(NewSiteBoxState.INSTALLED);
    },

    _onUrlEntryChanged: function() {
        if (this._state == NewSiteBoxState.SEARCHING || this._state == NewSiteBoxState.ERROR) {
            this._setState(NewSiteBoxState.READY)
        }

        // Show the '>' secondary icon in the entry when there's some text written.
        let iconName = (this._urlEntry.get_text().length > 0) ? 'go-next-symbolic' : null;
        this._urlEntry.secondary_icon_name = iconName;
    },

    _onUrlEntryActivated: function() {
        let url = this._urlEntry.get_text();
        this._webHelper = new NewSiteHelper(url);

        this._webHelper.connect('favicon-loaded', Lang.bind(this, this._onFaviconLoaded));
        this._webHelper.connect('website-loaded', Lang.bind(this, this._onWebsiteLoaded));
        this._webHelper.connect('website-failed', Lang.bind(this, this._onWebsiteFailed));

        this._setState(NewSiteBoxState.SEARCHING);
    },

    _onFaviconLoaded: function(webHelper) {
        this._siteIcon.set_from_pixbuf(webHelper.favicon);
    },

    _onWebsiteLoaded: function() {
        this._setState(NewSiteBoxState.FOUND);
    },

    _onSiteAlertEnterEvent: function() {
        if (this._state == NewSiteBoxState.FOUND) {
            this._siteAlertLabelEventBox.get_style_context().add_class('alert-highlight');
        }
    },

    _onSiteAlertLeaveEvent: function() {
        this._siteAlertLabelEventBox.get_style_context().remove_class('alert-highlight');
    },

    _onSiteAlertLabelClicked: function() {
        this._setState(NewSiteBoxState.EMPTY);
    },

    _onWebsiteFailed: function() {
        this._setState(NewSiteBoxState.ERROR);
    }
});
Builder.bindTemplateChildren(NewSiteBox.prototype);

const WeblinkListBoxRow = new Lang.Class({
    Name: 'WeblinkListBoxRow',
    Extends: Gtk.EventBox,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-list-row.ui',
    templateChildren: [
        '_mainBox',
        '_icon',
        '_nameLabel',
        '_descriptionLabel',
        '_labelsBox',
        '_stateButton'
    ],

    _init: function(parentFrame, model, row) {
        this.parent();

        this._parentFrame = parentFrame;
        this._model = model;
        this._row = row;
        this._info = row.linkInfo;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);

        this._nameLabel.set_text(this._info.get_title());
        this._descriptionLabel.set_text(this._info.get_description());

        let installedSensitive = (!this._model.hasLauncher(this._info.get_desktop_id()));
        this._setSensitiveState(installedSensitive);
        this._mainBox.show();
    },

    _setSensitiveState: function(isSensitive) {
        if (isSensitive) {
            this._stateButton.sensitive = true;
        } else {
            this._stateButton.sensitive = false;
        }
    },

    // This 'just installed' state should go away after closing the store and
    // opening it again, by restoring the original screenshot and description.
    _setJustInstalledState: function() {
        this._descriptionLabel.set_text(_("added successfully!"));

        let iconName = this._info.get_icon_name();
        this._icon.set_from_icon_name(iconName, Gtk.IconSize.DIALOG);
        this._row.show_icon = true;
    },

    _onStateButtonClicked: function() {
        this._parentFrame.setModelConnected(false);

        let desktopId = this._info.get_desktop_id();
        this._model.install(desktopId, function() {});

        this._setSensitiveState(false);
        this._setJustInstalledState();

        GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,
                                 NEW_SITE_SUCCESS_TIMEOUT,
                                 Lang.bind(this, function() {
                                     this._parentFrame.setModelConnected(true);
                                     return false;
                                 }));
    },
});
Builder.bindTemplateChildren(WeblinkListBoxRow.prototype);

const WeblinkListBox = new Lang.Class({
    Name: 'WeblinkListBox',
    Extends: Gtk.ListBox,

    _init: function(model) {
        this.parent({ selection_mode: Gtk.SelectionMode.NONE });
        this.get_style_context().add_class('weblink-listbox');
        this._model = model;
    }
});

const WeblinkListBoxRowSeparator = new Lang.Class({
    Name: 'WeblinkListBoxRowSeparator',
    Extends: Gtk.Frame,

    _init: function() {
        this.parent();
        this.get_style_context().add_class('list-row-separator');
    }
});

const WeblinkFrame = new Lang.Class({
    Name: 'WeblinkFrame',
    Extends: Gtk.Frame,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-frame.ui',
    templateChildren: [
        '_mainBox',
        '_newSiteFrame',
        '_categoriesBox',
        '_listFrame',
    ],

    _init: function(mainWindow) {
        this.parent();

        this.get_style_context().add_class('web-frame');

        this._categories = Categories.get_link_categories();

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);

        let description = new Gtk.Label({ label: _("Add your favorite websites to your desktop or choose suggested ones from our list.") });
        description.get_style_context().add_class('weblink-description');
        description.set_alignment(0, 0.5);
        this._mainBox.add(description);
        this._mainBox.reorder_child(description, 0);

        let separator = new Separator.FrameSeparator();
        this._mainBox.add(separator);
        this._mainBox.reorder_child(separator, 3);

        this._mainBox.show_all();

        if (mainWindow.getExpectedWidth() <= AppStoreWindow.AppStoreSizes.SVGA.screenWidth) {
            this._columns = 1;
        } else {
            this._columns = 2;
        }

        this._weblinkListModel = new AppListModel.WeblinkList();

        this._newSiteBox = new NewSiteBox(this._weblinkListModel);
        this._newSiteFrame.add(this._newSiteBox);

        this._stack = new Gtk.Stack({ transition_duration: CATEGORY_TRANSITION_MS,
                                      transition_type: Gtk.StackTransitionType.SLIDE_RIGHT,
                                      hexpand: true,
                                      vexpand: true });
        this._listFrame.add(this._stack);

        this._mainBox.show_all();

        this._currentCategory = this._categories[0].name;
        this._currentCategoryIdx = 0;

        this._buttonGroup = null;
        this._modelConnectionId = null;
        this._populateCategoryHeaders();
        this.setModelConnected(true);

        let content_dir = EosAppStorePrivate.link_get_content_dir();
        let content_path = GLib.build_filenamev([content_dir, 'content.json']);
        let content_file = Gio.File.new_for_path(content_path);
        this._contentMonitor = content_file.monitor_file(Gio.FileMonitorFlags.NONE, null);
        this._contentMonitor.connect('changed', Lang.bind(this, this._repopulate));

        // We want all the links to recover their original state (screenshot and description)
        // after hiding the store, regardless they have been recently installed or not.
        mainWindow.connect('hide', Lang.bind(this, this._repopulate));
    },

    _repopulate: function(monitor, file, other_file, event_type) {
        this._populateAllCategories();

        this._stack.transition_type = Gtk.StackTransitionType.NONE;
        this._stack.set_visible_child_name(this._currentCategory);
    },

    setModelConnected: function(connect) {
        // Ensure that we don't connect to the 'changed' signal from the model more than
        // once at the same time by always disconnecting from it first if needed.
        if (this._modelConnectionId) {
            this._weblinkListModel.disconnect(this._modelConnectionId);
            this._modelConnectionId = null;
        }

        if (connect) {
            this._modelConnectionId = this._weblinkListModel.connect('changed', Lang.bind(this, this._repopulate));
        }
    },

    _populateCategoryHeaders: function() {
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
       }
    },

    _resetCategory: function(categoryId) {
        let category = this._categories[categoryId];

        if (category.widget) {
            category.widget.destroy();
            category.widget = null;
        }
    },

    _populateCategory: function(categoryId) {
        let category = this._categories[categoryId];

        if (category.widget) {
            return;
        }

        let scrollWindow;
        scrollWindow = new Gtk.ScrolledWindow({ hscrollbar_policy: Gtk.PolicyType.NEVER,
                                                vscrollbar_policy: Gtk.PolicyType.AUTOMATIC,
                                                shadow_type: Gtk.ShadowType.IN });
        scrollWindow.get_style_context().add_class('weblink-scrolledwindow');
        this._stack.add_named(scrollWindow, category.name);
        category.widget = scrollWindow;

        let weblinksBox = new Gtk.Box({ orientation: Gtk.Orientation.HORIZONTAL,
                                        homogeneous: true,
                                        spacing: LIST_COLUMNS_SPACING });
        scrollWindow.add_with_viewport(weblinksBox);

        let weblinksColumnBoxes = [];
        for (let i = 0; i < this._columns; i++) {
            weblinksColumnBoxes[i] = new WeblinkListBox(this._weblinkListModel);
            weblinksColumnBoxes[i].set_header_func(Lang.bind(this, this._updateColumnBoxHeader));
            weblinksBox.add(weblinksColumnBoxes[i]);
        }

        let cells = EosAppStorePrivate.link_load_content(category.id);
        let index = 0;
        for (let i in cells) {
            let info = cells[i];
            let row = info.create_row();
            let rowContent = new WeblinkListBoxRow(this, this._weblinkListModel, row);
            row.add(rowContent);
            weblinksColumnBoxes[(index++)%this._columns].add(row);
        }

        scrollWindow.show_all();
    },

    _populateAllCategories: function() {
        for (let c in this._categories) {
            this._resetCategory(c);
            this._populateCategory(c);
        }
    },

    _updateColumnBoxHeader: function(row, before) {
        if (before) {
            row.set_header(new WeblinkListBoxRowSeparator());
        }
    },

    _onCategoryClicked: function(button) {
        let idx = button.index;
        let category = button.category;

        // Scroll to the top of the selected category
        let widget = this._categories[idx].widget;
        if (widget) {
            let vscrollbar = widget.get_vscrollbar();
            vscrollbar.set_value(0);
        }

        if (idx > this._currentCategoryIdx) {
            this._stack.transition_type = Gtk.StackTransitionType.SLIDE_LEFT;
        } else {
            this._stack.transition_type = Gtk.StackTransitionType.SLIDE_RIGHT;
        }

        this._currentCategoryIdx = idx;
        this._currentCategory = category;

        this._populateCategory(idx);

        this._stack.set_visible_child_name(category);
    },

    reset: function() {
        // Return to the first category
        this._buttonGroup.clicked();
    }
});
Builder.bindTemplateChildren(WeblinkFrame.prototype);
