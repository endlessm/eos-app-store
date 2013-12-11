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

const NEW_SITE_TITLE_LIMIT = 20;
const NEW_SITE_SUCCESS_TIMEOUT = 3;

const CATEGORY_TRANSITION_MS = 500;

const LIST_COLUMNS_SPACING = 10;

const DEFAULT_ICON = 'generic-link';
const EOS_BROWSER = 'chromium-browser ';
const DESKTOP_KEY_SPLASH = 'X-Endless-Splash-Screen';

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
    EDITING: 3,
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
        '_siteAlertLabel',
        '_siteAddButton'
    ],

    _init: function(weblinkListModel) {
        this.parent();

        this._webHelper = null;
        this._weblinkListModel = weblinkListModel;

        this._entryActivatedId = 0;
        this._entryChangedId = 0;

        this.initTemplate({ templateRoot: '_mainBox',
                            bindChildren: true,
                            connectSignals: true });
        this.add(this._mainBox);
        this._mainBox.show_all();

        this._alertIcons = [ null,
                             null,
                             new Gtk.Spinner({ name: 'spinner',
                                               width_request: 12,
                                               height_request: 12,
                                               margin: 4 }),
                             new Gtk.Button({ name: 'cancel' }),
                             new Gtk.Image({ name: 'alert' }),
                             null ];
        this._alertIcons[NewSiteBoxState.EDITING].connect('clicked', Lang.bind(this, this._onEditSiteCancel));

        this._urlEntry = new Gtk.Entry();
        this._urlEntry.set_placeholder_text(_("Write the site address you want to add"));
        this._urlEntry.get_style_context().add_class('url-entry');

        this._urlEntry.connect('enter-notify-event',
                               Lang.bind(this, function() {
                                   this._urlEntry.set_state_flags(Gtk.StateFlags.PRELIGHT, false);
                               }));

        this._urlEntry.connect('leave-notify-event',
                               Lang.bind(this, function() {
                                   this._urlEntry.unset_state_flags(Gtk.StateFlags.PRELIGHT);
                               }));

        this._siteUrlFrame.add(this._urlEntry);
        this._sitePixbuf = null;

        this._setState(NewSiteBoxState.EMPTY);
    },

    _setState: function(state) {
        if (this._state == state) {
            return;
        }

        // Clean up common state
        if (this._entryActivateId > 0) {
            this._urlEntry.disconnect(this._entryActivateId);
            this._entryActivateId = 0;
        }

        if (this._entryChangedId > 0) {
            this._urlEntry.disconnect(this._entryChangedId);
            this._entryChangedId = 0;
        }

        let prevState = this._state;
        this._state = state;
        this._switchAlertIcon(prevState);

        switch (state) {
        case NewSiteBoxState.EMPTY:
            this._urlEntry.set_text('');
            this._urlEntry.grab_focus();
            // fall through
        case NewSiteBoxState.READY:
            this._siteAlertLabel.set_text(_("e.g.: http://www.globoesporte.com"));

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

            this._entryActivateId = this._urlEntry.connect('activate',
                                                           Lang.bind(this, this._onUrlEntryActivated));

            break;
        case NewSiteBoxState.SEARCHING:
            this._siteAlertLabel.set_text(_("searching"));

            this._urlEntry.get_style_context().remove_class('url-entry-error');

            this._entryChangedId = this._urlEntry.connect('changed',
                                                          Lang.bind(this, this._onUrlEntryChanged));

            break;
        case NewSiteBoxState.EDITING:
            this._siteAlertLabel.set_text(this._webHelper.url);

            this._siteAddButton.visible = true;

            // Narrow the entry and put the focus so user can change the title
            this._urlEntry.max_length = NEW_SITE_TITLE_LIMIT;
            this._urlEntry.halign = Gtk.Align.START;
            this._urlEntry.set_text(this._webHelper.title);

            break;
        case NewSiteBoxState.ERROR:
            this._siteAlertLabel.set_text(_("The address written does not exist or is not available."));

            this._urlEntry.get_style_context().add_class('url-entry-error');

            this._entryChangedId = this._urlEntry.connect('changed',
                                                          Lang.bind(this, this._onUrlEntryChanged));

            break;
        case NewSiteBoxState.INSTALLED:
            this._siteAlertLabel.set_text(_("added successfully!"));

            let urlLabel = new Gtk.Label({ label: this._urlEntry.get_text() });
            urlLabel.get_style_context().add_class('url-label');
            urlLabel.set_alignment(0, 0.5);
            this._siteUrlFrame.remove(this._urlEntry);
            this._siteUrlFrame.add(urlLabel);
            this._siteUrlFrame.show_all();

            this._siteAddButton.sensitive = false;

            GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,
                                     NEW_SITE_SUCCESS_TIMEOUT,
                                     Lang.bind(this, function() {
                                         this._siteUrlFrame.remove(urlLabel);
                                         this._siteUrlFrame.add(this._urlEntry);
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
            this._siteAlertIconFrame.visible = true;
            this._siteAlertIconFrame.add(alertIcon);
            alertIcon.show();

            if (this._state == NewSiteBoxState.SEARCHING) {
                alertIcon.start();
            }
        } else {
            this._siteAlertIconFrame.visible = false;
        }
    },

    _onEditSiteCancel: function() {
        this._setState(NewSiteBoxState.EMPTY);
    },

    _onSiteAdd: function() {
        let title = this._urlEntry.get_text();

        let desktopId = this._webHelper.save(title);
        this._weblinkListModel.install(desktopId, function() {});

        this._setState(NewSiteBoxState.INSTALLED);
    },

    _onUrlEntryChanged: function() {
        this._setState(NewSiteBoxState.READY);
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
        this._setState(NewSiteBoxState.EDITING);
    },

    _onWebsiteFailed: function() {
        this._setState(NewSiteBoxState.ERROR);
    }
});
Builder.bindTemplateChildren(NewSiteBox.prototype);

const TwoLinesLabel = new Lang.Class({
    Name: 'TwoLinesLabel',
    Extends: Gtk.Label,

    vfunc_draw: function(cr) {
        // override this here, as GtkLabel can invalidate and
        // recreate the PangoLayout at any time
        let layout = this.get_layout();
        layout.set_height(-2);

        let ret = this.parent(cr);
        cr.$dispose();
        return ret;
    },

    set_text: function(text) {
        // since we handle paragraphs internally, we don't want
        // new lines in the text
        let strippedText = text.replace('\n', ' ', 'gm');
        this.parent(strippedText);
    }
});

const WeblinkListBoxRow = new Lang.Class({
    Name: 'WeblinkListBoxRow',
    Extends: Gtk.ListBoxRow,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-list-row.ui',
    templateChildren: [
        '_mainBox',
        '_icon',
        '_nameLabel',
        '_labelsBox',
        '_urlLabel',
        '_urlIndicator',
        '_stateButton'
    ],

    _init: function(parentFrame, model, info) {
        this.parent();

        this._parentFrame = parentFrame;
        this._model = model;
        this._info = info;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);

        this._descriptionLabel = new TwoLinesLabel({ visible: true,
                                                     xalign: 0,
                                                     yalign: 0,
                                                     ellipsize: Pango.EllipsizeMode.END,
                                                     wrap: true,
                                                     wrap_mode: Pango.WrapMode.WORD_CHAR });
        this._descriptionLabel.get_style_context().add_class('description');
        this._labelsBox.pack_start(this._descriptionLabel, false, true, 0);
        this._labelsBox.reorder_child(this._descriptionLabel, 1);

        this._nameLabel.set_text(info.get_title());
        this._descriptionLabel.set_text(info.get_description());
        this._urlLabel.set_text(info.get_url());

        this._setButtonStates();
        this._mainBox.show();
    },

    _setButtonStates: function() {
        this._stateButton.connect('pressed', Lang.bind(this, function() {
            this._setPressState(true);
        }));

        this._stateButton.connect('released', Lang.bind(this, function() {
            this._setPressState(false);
        }));

        this._stateButton.connect('enter-notify-event', Lang.bind(this, function() {
            this._setHoverState(true);
        }));

        this._stateButton.connect('leave-notify-event', Lang.bind(this, function() {
            this._setHoverState(false);
        }));

        this._setSensitiveState(this._getState() != EosAppStorePrivate.AppState.INSTALLED);
    },

    vfunc_state_flags_changed: function(previousFlags) {
        this.parent(previousFlags);

        let flags = this.get_state_flags();
        let isHover = ((flags & Gtk.StateFlags.PRELIGHT) != 0);
        let icon = null;

        if (isHover) {
            this._setActiveState(true);
            let iconName = this._info.get_icon_name();
            this._icon.set_from_icon_name(iconName, Gtk.IconSize.DIALOG);
        } else {
            this._setActiveState(false);
            this._icon.clear();
        }
    },

    _getState: function() {
        let desktopId = this._info.get_desktop_id();
        return this._model.getState(desktopId);
    },

    _setActiveState: function(isActive) {
        if (isActive) {
            this._stateButton.get_style_context().add_class('state-button-active');
        } else {
            this._stateButton.get_style_context().remove_class('state-button-active');
        }
    },

    _setPressState: function(isPressed) {
        if (isPressed) {
            this._stateButton.get_style_context().add_class('state-button-pressed');
        } else {
            this._stateButton.get_style_context().remove_class('state-button-pressed');
        }
    },

    _setHoverState: function(isHovered) {
        if (isHovered) {
            this._stateButton.get_style_context().add_class('state-button-hover');
        } else {
            this._stateButton.get_style_context().remove_class('state-button-hover');
        }
    },

    _setSensitiveState: function(isSensitive) {
        if (isSensitive) {
            this._stateButton.sensitive = true;
        } else {
            this._stateButton.sensitive = false;
        }
    },

    _setInstalledState: function(installed, message) {
        this._nameLabel.vexpand = installed;
        this._urlLabel.visible = !installed;
        this._descriptionLabel.set_text(message);
    },

    _showInstalledMessage: function () {
        this._setSensitiveState(false);
        this._setInstalledState(true, _("added successfully!"));

        GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,
                                 NEW_SITE_SUCCESS_TIMEOUT,
                                 Lang.bind(this, function() {
                                     this._setInstalledState(false, this._info.get_description());
                                     this._parentFrame.setModelConnected(true);
                                     return false;
                                 }));
    },

    _onStateButtonClicked: function() {
        this._parentFrame.setModelConnected(false);

        let desktopId = this._info.get_desktop_id();
        this._model.install(desktopId, function() {});

        this._showInstalledMessage();
    },

    _onUrlClicked: function(widget, event) {
        Gtk.show_uri(null, this._info.get_url(), event.time, null);
        // hide the appstore to see the browser
        this.get_toplevel().emit('delete-event', null);
    },

    _onStartHoveringLabel: function() {
        this._urlIndicator.visible = true;
    },

    _onStopHoveringLabel: function() {
        this._urlIndicator.visible = false;
    }
});
Builder.bindTemplateChildren(WeblinkListBoxRow.prototype);

const WeblinkListBox = new Lang.Class({
    Name: 'WeblinkListBox',
    Extends: Gtk.ListBox,

    _init: function(model) {
        this.parent({ selection_mode: Gtk.SelectionMode.NONE });
        this.get_style_context().add_class("weblink-listbox");
        this._model = model;
    }
});

const WeblinkListBoxRowSeparator = new Lang.Class({
    Name: 'WeblinkListBoxRowSeparator',
    Extends: Gtk.Frame,

    _init: function() {
        this.parent();
        this.get_style_context().add_class("list-row-separator");
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

        let separator = new Separator.FrameSeparator();
        this._mainBox.add(separator);
        this._mainBox.reorder_child(separator, 2);

        this._mainBox.show_all();

        if (mainWindow.getExpectedWidth() <= AppStoreWindow.AppStoreSizes.XGA.windowWidth) {
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
        this.setModelConnected(true);

        let content_dir = EosAppStorePrivate.link_get_content_dir();
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

    setModelConnected: function(connect) {
        if (connect) {
            this._modelConnectionId = this._weblinkListModel.connect('changed', Lang.bind(this, this._populateCategories));
            this._populateCategories();
        } else if (this._modelConnectionId) {
            this._weblinkListModel.disconnect(this._modelConnectionId);
            this._modelConnectionId = null;
        }
    },

    _populateCategories: function() {
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
                                                        vscrollbar_policy: Gtk.PolicyType.AUTOMATIC,
                                                        shadow_type: Gtk.ShadowType.IN });
                scrollWindow.get_style_context().add_class('weblink-scrolledwindow');
                this._stack.add_named(scrollWindow, category.name);
                category.widget = scrollWindow;
            } else {
                scrollWindow = category.widget;
                let child = scrollWindow.get_child();
                child.destroy();
            }

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
                let rowContent = new WeblinkListBoxRow(this, this._weblinkListModel, info);
                row.add(rowContent);
                weblinksColumnBoxes[(index++)%this._columns].add(row);
            }

            scrollWindow.show_all();
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

        this._stack.set_visible_child_name(category);
    },

    reset: function() {
        // Return to the first category
        this._buttonGroup.clicked();
    }
});
Builder.bindTemplateChildren(WeblinkFrame.prototype);
