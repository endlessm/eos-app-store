// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Pango = imports.gi.Pango;
const PLib = imports.gi.PLib;
const WebKit = imports.gi.WebKit2;

const AppListModel = imports.appListModel;
const AppStoreWindow = imports.appStoreWindow;
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

const AlertIcon = {
    SPINNER: 0,
    CANCEL: 1,
    ERROR: 2,
    NOTHING: 3,
    HIDDEN: 4
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

        this._weblinkListModel = weblinkListModel;
        this._newSiteError = false;
        this._webView = null;
        this._alertIcon = null;
        this._currentAlertIcon = AlertIcon.NOTHING;

        this.initTemplate({ templateRoot: '_mainBox',
                            bindChildren: true,
                            connectSignals: true });
        this.add(this._mainBox);
        this._mainBox.show_all();

        this._createAlertIcons();
        this._switchAlertIcon(AlertIcon.NOTHING);

        this._urlEntry = new Gtk.Entry();
        this._urlEntry.set_placeholder_text(_("Write the site address you want to add"));
        this._urlEntry.get_style_context().add_class('url-entry');
        this._urlEntry.connect('activate', Lang.bind(this, this._onUrlEntryActivated));

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

        this._reset();
    },

    _createAlertIcons: function() {
        this._alertIcon = [ new Gtk.Spinner({ name: 'spinner' }),
                            new Gtk.Button({ name: 'cancel' }),
                            new Gtk.Image({ name: 'alert' }),
                            null ];

        this._alertIcon[AlertIcon.SPINNER].set_size_request(16, 16);
        this._alertIcon[AlertIcon.CANCEL].show_all();
        this._alertIcon[AlertIcon.CANCEL].connect('clicked', Lang.bind(this, this._onEditSiteCancel));
    },

    _reset: function() {
        this._siteAddButton.visible = false;
        this._switchAlertIcon(AlertIcon.NOTHING);
        this._siteAlertLabel.set_text(_("e.g.: http://www.globoesporte.com"));
        this._urlEntry.set_text("");
        this._urlEntry.max_length = 0;
        this._urlEntry.halign = Gtk.Align.FILL;
        this._urlEntry.grab_focus();
        this._sitePixbuf = null;

        // https://bugzilla.gnome.org/show_bug.cgi?id=709056
        let file = Gio.File.new_for_path(Path.ICONS_DIR + '/icon_website-symbolic.svg');
        let gicon = new Gio.FileIcon({ file: file });
        this._siteIcon.set_from_gicon(gicon, Gtk.IconSize.DND);
    },

    _switchAlertIcon: function(newItem) {
        if (this._currentAlertIcon == AlertIcon.SPINNER) {
            this._alertIcon[AlertIcon.SPINNER].stop();
        }

        if (this._currentAlertIcon != AlertIcon.NOTHING &&
            this._currentAlertIcon != AlertIcon.HIDDEN) {
            this._siteAlertIconFrame.remove(this._alertIcon[this._currentAlertIcon]);
        }

        this._currentAlertIcon = newItem;

        if (this._currentAlertIcon == AlertIcon.HIDDEN) {
            this._siteAlertIconFrame.visible = false;
        } else {
            this._siteAlertIconFrame.visible = true;
            if (this._currentAlertIcon != AlertIcon.NOTHING) {
                this._siteAlertIconFrame.add(this._alertIcon[this._currentAlertIcon]);
                this._alertIcon[this._currentAlertIcon].show();
            }
        }

        if (this._currentAlertIcon == AlertIcon.SPINNER) {
            this._alertIcon[AlertIcon.SPINNER].start();
        }
    },

    _editSite: function() {
        this._switchAlertIcon(AlertIcon.CANCEL);
        this._siteAddButton.visible = true;
        this._urlEntry.set_text(this._webView.get_title());
        this._siteAlertLabel.set_text(this._webView.get_uri());

        // Narrow the entry and put the focus so user can change the title
        let [entryWidth, entryHeight] = this._urlEntry.get_size_request();
        this._urlEntry.max_length = NEW_SITE_TITLE_LIMIT;
        this._urlEntry.halign = Gtk.Align.START;
    },

    _showInstalledMessage: function() {
        let urlLabel = new Gtk.Label({ label: this._urlEntry.get_text() });
        urlLabel.get_style_context().add_class('url-label');
        urlLabel.set_alignment(0, 0.5);
        this._siteUrlFrame.remove(this._urlEntry);
        this._siteUrlFrame.add(urlLabel);
        this._siteUrlFrame.show_all();

        this._siteAlertLabel.set_text(_("added successfully!"));
        this._siteAddButton.sensitive = false;
        this._switchAlertIcon(AlertIcon.HIDDEN);

        GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,
                                 NEW_SITE_SUCCESS_TIMEOUT,
                                 Lang.bind(this, function() {
                                     this._siteUrlFrame.remove(urlLabel);
                                     this._siteUrlFrame.add(this._urlEntry);
                                     this._urlEntry.sensitive = true;
                                     this._siteAddButton.sensitive = true;
                                     this._reset();
                                     return false;
                                 }));
    },

    _onEditSiteCancel: function() {
        this._reset();
    },

    _onSiteAdd: function() {
        let url = this._siteAlertLabel.get_text();
        let title = this._urlEntry.get_text();

        let weblinkIcon = DEFAULT_ICON;
        if (this._sitePixbuf) {
            weblinkIcon = this._weblinkListModel.saveIcon(this._sitePixbuf, "png");
        }

        let newSite = this._weblinkListModel.createWeblink(url, title, weblinkIcon);
        this._weblinkListModel.update();
        this._weblinkListModel.install(newSite, function() {});

        this._showInstalledMessage();
    },

    _onUrlEntryActivated: function() {
        if (!this._webView) {
            this._webView = new WebKit.WebView();
            let context = this._webView.get_context();
            let cachePath = GLib.build_filenamev([GLib.get_user_cache_dir(),
                                                  'eos-app-store', 'icondatabase']);
            context.set_favicon_database_directory(cachePath);
            this._webView.connect('load-changed', Lang.bind(this, this._onLoadChanged));
            this._webView.connect('load-failed', Lang.bind(this, this._onLoadFailed));
            this._webView.connect('notify::favicon', Lang.bind(this, this._onFaviconLoaded));
        }
        this._urlEntry.get_style_context().remove_class('url-entry-error');
        let url = this._urlEntry.get_text();

        // check if the URL that the user entered already has a valid prefix
        if (url.indexOf('http://') != 0 && url.indexOf('https://') != 0 &&
            url.indexOf('ftp://')  != 0 && url.indexOf('file://')  != 0) {
            //if it does not start with a valid prefix, prepend http://
            url = 'http://' + url;
        }

        this._webView.load_uri(url);
    },

    _onFaviconLoaded: function() {
        let favicon = EosAppStorePrivate.link_get_favicon(this._webView);
        if (favicon) {
            this._sitePixbuf = favicon;
            this._siteIcon.set_from_pixbuf(favicon);
        }
    },

    _onLoadChanged: function(webview, loadEvent) {
        switch (loadEvent) {
        case WebKit.LoadEvent.STARTED:
            this._switchAlertIcon(AlertIcon.SPINNER);
            this._siteAlertLabel.set_text(_("searching"));
            this._newSiteError = false;
            break;
        case WebKit.LoadEvent.FINISHED:
            // Error this was processed on 'load-failed' handler
            if (this._newSiteError) {
                return;
            }

            this._editSite();
            break;
        }
    },

    _onLoadFailed: function() {
        this._newSiteError = true;
        this._siteAlertLabel.set_text(_("The address written does not exist or is not available."));
        this._switchAlertIcon(AlertIcon.ERROR);
        this._urlEntry.get_style_context().add_class('url-entry-error');
        return true;
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

        return this.parent(cr);
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
    Extends: Gtk.Bin,

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

        this._setSensitiveState(this._getStateFromUrl() != EosAppStorePrivate.AppState.INSTALLED);
    },

    vfunc_state_flags_changed: function(previousFlags) {
        this.parent(previousFlags);

        let flags = this.get_state_flags();
        let isHover = ((flags & Gtk.StateFlags.PRELIGHT) != 0);
        let icon = null;

        if (isHover) {
            this._setActiveState(true);
            icon = this._info.get_icon();
            if (icon) {
                this._icon.set_from_pixbuf(icon);
            } else {
                this._icon.set_from_icon_name(DEFAULT_ICON, Gtk.IconSize.DIALOG);
            }
        } else {
            this._setActiveState(false);
            this._icon.clear();
        }
    },

    // FIXME: this should be entirely unnecessary, as we could just use
    // the linkId, and call getState() on WeblinkList with that ID.
    // Unfortunately, the CMS-provided content is broken for weblinks
    // right now, and it has a NULL linkId to all values.
    // See https://github.com/endlessm/eos-shell/issues/1074
    _getStateFromUrl: function() {
        let url = this._info.get_url();
        let id = this._model.getWeblinkForUrl(url);

        if (id) {
            return EosAppStorePrivate.AppState.INSTALLED;
        } else {
            return EosAppStorePrivate.AppState.UNINSTALLED;
        }
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

        let url = this._info.get_url();
        let title = this._info.get_title();
        let icon = this._info.get_icon_filename();
        if (!icon) {
            icon = DEFAULT_ICON;
        }

        let site = this._model.createWeblink(url, title, icon);
        this._model.install(site, function() {});

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
    Extends: PLib.ListBox,

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

        this._categories = [
            {
                name: 'news',
                widget: null,
                label: _("News"),
                id: EosAppStorePrivate.LinkCategory.NEWS,
            },
            {
                name: 'sports',
                widget: null,
                label: _("Sports"),
                id: EosAppStorePrivate.LinkCategory.SPORTS,
            },
            {
                name: 'education',
                widget: null,
                label: _("Education and Health"),
                id: EosAppStorePrivate.LinkCategory.EDUCATION,
            },
            {
                name: 'entertainment',
                widget: null,
                label: _("Entertainment"),
                id: EosAppStorePrivate.LinkCategory.ENTERTAINMENT,
            },
            {
                name: 'local',
                widget: null,
                label: _("Local"),
                id: EosAppStorePrivate.LinkCategory.LOCAL,
            }
        ];

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

        this._stack = new PLib.Stack({ transition_duration: CATEGORY_TRANSITION_MS,
                                       transition_type: PLib.StackTransitionType.SLIDE_RIGHT,
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
            this._stack.transition_type = PLib.StackTransitionType.SLIDE_LEFT;
        } else {
            this._stack.transition_type = PLib.StackTransitionType.SLIDE_RIGHT;
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
