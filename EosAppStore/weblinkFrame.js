// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Pango = imports.gi.Pango;
const Soup = imports.gi.Soup;
const WebKit = imports.gi.WebKit2;

const AppStorePages = imports.appStorePages;
const AppStoreWindow = imports.appStoreWindow;
const Categories = imports.categories;
const CategoryButton = imports.categoryButton;
const Builder = imports.builder;
const Lang = imports.lang;
const Path = imports.path;
const Separator = imports.separator;
const Signals = imports.signals;

const NEW_SITE_SUCCESS_TIMEOUT = 3;

const CATEGORY_TRANSITION_MS = 250;

const LIST_COLUMNS_SPACING = 10;

const DEFAULT_ICON = 'generic-link';
const EOS_BROWSER = 'chromium-browser ';
const DESKTOP_KEY_MAXIMIZED = 'X-Endless-LaunchMaximized';

const ICON_EXTERNAL_LINK = '/com/endlessm/appstore/icon_external-link.png';
const ICON_BLANK = '/com/endlessm/appstore/icon_blank.png';

const JUST_INSTALLED_TIMEOUT = 500; // ms

function getAvailableFilename(path, prefix, name, suffix) {
    let filename = prefix + name;

    // Append a number until we find a free slot
    let availableFilename = filename + suffix;
    let availablePath = GLib.build_filenamev([path, availableFilename]);
    let index = 0;

    while (GLib.file_test(availablePath, GLib.FileTest.EXISTS)) {
        index++;
        availableFilename = filename + '-' + index + suffix;
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
    desktop.set_boolean(GLib.KEY_FILE_DESKTOP_GROUP, DESKTOP_KEY_MAXIMIZED, true);
    desktop.set_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_NAME, title);

    let [data, length] = desktop.to_data();
    GLib.file_set_contents(availablePath, data, length);

    return [availablePath, desktop];
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

        this._webView.connect('load-changed', Lang.bind(this, this._onLoadChanged));
        this._webView.connect('load-failed', Lang.bind(this, this._onLoadFailed));
        this._webView.connect('notify::title', Lang.bind(this, this._onTitleChanged));
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

    _onTitleChanged: function() {
        let title = this._webView.title;
        if (title) {
            this._title = title;
            this.emit('title-changed');
        }
    },

    _onLoadChanged: function(webView, loadEvent) {
        if (loadEvent == WebKit.LoadEvent.FINISHED) {
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
        let title = this._title;
        if (!title) {
            // Some pages do not provide a title so we need to craft something
            // ourselves in order to show something and not keep waiting forever.
            // Let's use the 'host/path' part, at least not to show the raw URL.
            let soupURI = new Soup.URI(this._url);
            title = soupURI.get_host() + soupURI.get_path();
        }

        return title;
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

        let [keyfilePath, keyfile] = createWeblink(this._url, title, icon);
        this._savedKeyfile = keyfile;
        this._savedKeyfilePath = keyfilePath;

        // Return the desktop ID
        return GLib.basename(this._savedKeyfilePath);
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

    _init: function(shellProxy) {
        this.parent();

        this._webHelper = null;
        this._shellProxy = shellProxy;

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

        this._buildWidgetsForSiteUrlFrame();
        this._setSiteUrlFrameChild(this._urlEntry);

        this._setState(NewSiteBoxState.EMPTY);
    },

    _buildWidgetsForSiteUrlFrame: function() {
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
                               Lang.bind(this, this._onUrlEntryActivated));

        this._urlLabel = new Gtk.Label();
        this._urlLabel.get_style_context().add_class('url-label');
        this._urlLabel.set_ellipsize(Pango.EllipsizeMode.END);
        this._urlLabel.set_alignment(0, 0);
        this._urlLabel.show();

        this._siteAlertLabelEventBox.connect('enter-notify-event',
                                             Lang.bind(this, this._onSiteAlertEnterEvent));
        this._siteAlertLabelEventBox.connect('leave-notify-event',
                                             Lang.bind(this, this._onSiteAlertLeaveEvent));
        this._siteAlertLabelEventBox.connect('button-press-event',
                                             Lang.bind(this, this._onSiteAlertLabelClicked));
    },

    _setSiteUrlFrameChild: function(child) {
        let curChild = this._siteUrlFrame.get_child();
        if (child != curChild) {
            if (curChild) {
                this._siteUrlFrame.remove(curChild);
            }

            this._siteUrlFrame.add(child);
            child.show();
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
        this._siteAlertLabelEventBox.get_style_context().remove_class('alert-highlight');

        switch (state) {
        case NewSiteBoxState.EMPTY:
            this._urlEntry.set_text('');
            this._urlEntry.grab_focus();
            // fall through
        case NewSiteBoxState.READY:
            this._siteAlertLabel.set_text(_("e.g.: http://www.endlessm.com"));

            this._siteAddButton.visible = false;
            this._urlEntry.max_length = 0;
            this._urlEntry.halign = Gtk.Align.FILL;
            this._setSiteUrlFrameChild(this._urlEntry);

            this._sitePixbuf = null;

            let file = Gio.File.new_for_uri('resource:///com/endlessm/appstore/icon_website-symbolic.svg');
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
            this._setSiteUrlFrameChild(this._urlEntry);

            break;
        case NewSiteBoxState.FOUND:
            this._urlLabel.set_label(this._webHelper.title);
            this._setSiteUrlFrameChild(this._urlLabel);
            this._siteAlertLabel.set_text(this._webHelper.url);
            this._siteAddButton.visible = true;
            this._urlEntry.secondary_icon_name = null;

            break;
        case NewSiteBoxState.ERROR:
            this._siteAlertLabel.set_text(_("The address written does not exist or is not available."));
            this._urlEntry.secondary_icon_name = null;
            this._urlEntry.get_style_context().add_class('url-entry-error');
            this._setSiteUrlFrameChild(this._urlEntry);

            break;
        case NewSiteBoxState.INSTALLED:
            this._urlLabel.set_label(this._webHelper.title);
            this._setSiteUrlFrameChild(this._urlLabel);
            this._siteAlertLabel.set_text(_("Added successfully!"));
            this._siteAddButton.sensitive = false;

            GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,
                                     NEW_SITE_SUCCESS_TIMEOUT,
                                     Lang.bind(this, function() {
                                         this._setSiteUrlFrameChild(this._urlEntry);
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
        // width request does not get the alert label misaligned in this case.
        this._siteAlertIconFrame.visible = (this._state != NewSiteBoxState.INSTALLED);
    },

    _onFoundSiteBack: function() {
        this._setState(NewSiteBoxState.EMPTY);
    },

    _onSiteAdd: function() {
        let title = this._urlLabel.get_label();

        let desktopID = this._webHelper.save(title);
        this._shellProxy.AddApplicationRemote(desktopID);

        this._setState(NewSiteBoxState.INSTALLED);

        // UX here is pretty bad if we leave the app store on top
        let application = Gio.Application.get_default();
        application.hideIfVisible();
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
        this._webHelper.connect('title-changed', Lang.bind(this, this._onTitleChanged));
        this._webHelper.connect('website-loaded', Lang.bind(this, this._onWebsiteLoaded));
        this._webHelper.connect('website-failed', Lang.bind(this, this._onWebsiteFailed));

        this._setState(NewSiteBoxState.SEARCHING);
    },

    _onFaviconLoaded: function(webHelper) {
        this._siteIcon.set_from_pixbuf(webHelper.favicon);
    },

    _onTitleChanged: function(webHelper) {
        // We mark the site as FOUND as soon as we have a title to look
        // more responsive, so that we don't have to wait for the full
        // URL to finish loading in cases where a title is provided.
        this._setState(NewSiteBoxState.FOUND);
    },

    _onWebsiteLoaded: function() {
        // We need to mark the URL as FOUND whenever a load finishes, so that
        // we make sure we don't end up waiting forever when there's no title.
        if (this._state != NewSiteBoxState.ERROR) {
            this._setState(NewSiteBoxState.FOUND);
        }
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

    _init: function(row, shellProxy, appsOnDesktop) {
        this.parent();

        this._row = row;
        this._info = row.linkInfo;

        this._shellProxy = shellProxy;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);

        this._nameLabel.set_text(this._info.get_title());
        this._descriptionLabel.set_text(this._info.get_description());

        this._setSensitiveState(!this._isOnDesktop(appsOnDesktop));
        this._mainBox.show();
    },

    _setSensitiveState: function(isSensitive) {
        this._stateButton.sensitive = isSensitive;
    },

    _isOnDesktop: function(appsOnDesktop) {
        for (let i = 0; i < appsOnDesktop.length; i++) {
            if (appsOnDesktop[i] == this._info.get_desktop_id())
                return true;
        }
        return false;
    },

    // This 'just installed' state should go away after closing the store and
    // opening it again, by restoring the original screenshot and description.
    _setJustInstalledState: function() {
        this._descriptionLabel.set_text(_("Added successfully!"));

        let iconName = this._info.get_icon_name();
        this._icon.set_from_icon_name(iconName, Gtk.IconSize.DIALOG);
        this._row.show_icon = true;
    },

    _onStateButtonClicked: function() {
        let desktopId = this._info.get_desktop_id();
        this._shellProxy.AddApplicationRemote(desktopId);

        this._setSensitiveState(false);
        this._setJustInstalledState();

        // We hide the AppStore after a small delay so the user
        // sees the just installed state
        GLib.timeout_add(GLib.PRIORITY_DEFAULT,
                         JUST_INSTALLED_TIMEOUT,
                         Lang.bind(this, function() {
                             let app = Gio.Application.get_default();
                             app.hideIfVisible();
                             return false;
                         }));
    },
});
Builder.bindTemplateChildren(WeblinkListBoxRow.prototype);

const WeblinkListBox = new Lang.Class({
    Name: 'WeblinkListBox',
    Extends: Gtk.ListBox,

    _init: function() {
        this.parent({ selection_mode: Gtk.SelectionMode.NONE });
        this.get_style_context().add_class('weblink-listbox');
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
    Implements: [AppStorePages.AppStorePageProvider],

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-frame.ui',
    templateChildren: [
        '_categoriesBox',
        '_listFrame',
        '_mainBox',
        '_newSiteFrame'
    ],

    _init: function() {
        this.parent({ visible: true });

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.get_style_context().add_class('web-frame');
        this.add(this._mainBox);

        let app = Gio.Application.get_default();
        this._shellProxy = app.shellProxy.proxy;

        this._initCategories();
        this._updateAppsOnDesktop();

        if (app.mainWindow.getExpectedWidth() <= AppStoreWindow.AppStoreSizes.SVGA.screenWidth) {
            this._columns = 1;
        } else {
            this._columns = 2;
        }

        // We want all the links to recover their original state (screenshot and description)
        // after hiding the store, regardless they have been recently installed or not.
        app.mainWindow.connect('hide', Lang.bind(this, this._repopulate));

        let description = new Gtk.Label({ label: _("Add your favorite websites to your desktop or choose suggested ones from our list."),
                                          max_width_chars: 60,
                                          xalign: 0 });
        description.get_style_context().add_class('weblink-description');
        description.set_line_wrap(true);
        this._mainBox.add(description);
        this._mainBox.reorder_child(description, 0);

        let separator = new Separator.FrameSeparator();
        this._mainBox.add(separator);
        this._mainBox.reorder_child(separator, 3);

        this._newSiteBox = new NewSiteBox(this._shellProxy);
        this._newSiteFrame.add(this._newSiteBox);

        this._stack = new Gtk.Stack({ transition_duration: CATEGORY_TRANSITION_MS,
                                      transition_type: Gtk.StackTransitionType.SLIDE_RIGHT,
                                      hexpand: true,
                                      vexpand: true });
        this._listFrame.add(this._stack);

        this._mainBox.show_all();
    },

    // FIXME: Connect to ApplicationsChanged so we notice if something gets removed.
    _updateAppsOnDesktop: function() {
        this._appsOnDesktop = [];
        let [apps] = this._shellProxy.ListApplicationsSync();
        for (let i = 0; i < apps.length; i++) {
            // ListApplications returns apps in the shell's IconGridLayout,
            // but they might not actually be installed. Check.
            let info = Gio.DesktopAppInfo.new(apps[i]);
            if (info != null)
                this._appsOnDesktop.push(apps[i]);
        }
    },

    _initCategories: function() {
        let buttonGroup = null;
        this._categories = Categories.get_link_categories();
        this._currentCategoryIdx = 0;

        for (let idx in this._categories) {
            let category = this._categories[idx];
            category.links = EosAppStorePrivate.link_load_content(category.id);

            // We omit empty categories
            if (category.links.length == 0) {
                continue;
            }

            category.button = new CategoryButton.CategoryButton({ label: category.label,
                                                                  index: idx,
                                                                  category: category.name,
                                                                  draw_indicator: false,
                                                                  group: buttonGroup,
                                                                  visible: true });
            category.button.connect('clicked', Lang.bind(this, this._onButtonClicked));
            this._categoriesBox.add(category.button);

            if (!buttonGroup) {
                buttonGroup = category.button;
            }
        }
    },

    _populateCategory: function(idx) {
        let category = this._categories[idx];
        if (category.widget) {
            return category.widget;
        }

        let scrollWindow = new Gtk.ScrolledWindow({ hscrollbar_policy: Gtk.PolicyType.NEVER,
                                                    vscrollbar_policy: Gtk.PolicyType.AUTOMATIC,
                                                    shadow_type: Gtk.ShadowType.IN });
        scrollWindow.get_style_context().add_class('weblink-scrolledwindow');
        this._stack.add_named(scrollWindow, category.name);
        category.widget = scrollWindow;

        let weblinksBox = new Gtk.Box({ orientation: Gtk.Orientation.HORIZONTAL,
                                        homogeneous: true,
                                        spacing: LIST_COLUMNS_SPACING });
        scrollWindow.add(weblinksBox);

        let weblinksColumnBoxes = [];
        for (let i = 0; i < this._columns; i++) {
            weblinksColumnBoxes[i] = new WeblinkListBox();
            weblinksColumnBoxes[i].set_header_func(function(row, before) {
                if (before) {
                    row.set_header(new WeblinkListBoxRowSeparator());
                }
            });
            weblinksBox.add(weblinksColumnBoxes[i]);
        }

        let index = 0;
        for (let link_index in category.links) {
            let info = category.links[link_index];
            let row = info.create_row();
            let rowContent = new WeblinkListBoxRow(row, this._shellProxy, this._appsOnDesktop);
            row.add(rowContent);
            weblinksColumnBoxes[(index++)%this._columns].add(row);
        }

        scrollWindow.show_all();
        return category.widget;
    },

    _onButtonClicked: function(button) {
        let widget = this._populateCategory(button.index);

        // Scroll to the top of the selected category
        let vscrollbar = widget.get_vscrollbar();
        vscrollbar.set_value(0);

        if (button.index > this._currentCategoryIdx) {
            this._stack.transition_type = Gtk.StackTransitionType.SLIDE_LEFT;
        } else {
            this._stack.transition_type = Gtk.StackTransitionType.SLIDE_RIGHT;
        }

        this._currentCategoryIdx = button.index;
        this._stack.set_visible_child(widget);
    },

    _resetCategory: function(idx) {
        let category = this._categories[idx];
        if (category.widget) {
            category.widget.destroy();
            category.widget = null;
        }
    },

    _repopulate: function() {
        for (let idx in this._categories) {
            this._resetCategory(idx);
        }

        this.populate();
    },

    reset: function() {
        // Return to the first category
        this._categories[0].button.clicked();
    },

    createPage: function(pageId) {
        return this;
    },

    getPageIds: function() {
        return ['web'];
    },

    getIcon: function() {
        return 'resource:///com/endlessm/appstore/icon_web-symbolic.svg';
    },

    getName: function() {
        return _("Websites");
    },

    getTitle: function() {
        return _("Install websites");
    },

    populate: function() {
        let widget = this._populateCategory(this._currentCategoryIdx);
        this._stack.transition_type = Gtk.StackTransitionType.NONE;
        this._stack.set_visible_child(widget);

        this.show_all();
    },

    get canSearch() {
        return false;
    }
});
Builder.bindTemplateChildren(WeblinkFrame.prototype);
