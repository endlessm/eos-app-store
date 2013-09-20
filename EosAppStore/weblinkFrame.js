// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const PLib = imports.gi.PLib;
const WebKit = imports.gi.WebKit2;

const AppListModel = imports.appListModel;
const Builder = imports.builder;
const Lang = imports.lang;
const Signals = imports.signals;

const NEW_SITE_TITLE_LIMIT = 20;
const NEW_SITE_SUCCESS_TIMEOUT = 3;

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
        this._siteAlertLabel.set_text(_("e.g.: http://wwww.globoesporte.com"));
        this._urlEntry.set_text("");
        this._urlEntry.max_length = 0;
        this._urlEntry.halign = Gtk.Align.FILL;
        this._urlEntry.grab_focus();
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

    _onEditSiteCancel: function() {
        this._reset();
    },

    _onSiteAdd: function() {
        let url = this._siteAlertLabel.get_text();
        let title = this._urlEntry.get_text();

        let urlLabel = new Gtk.Label({ label: title });
        urlLabel.get_style_context().add_class('url-label');
        urlLabel.set_alignment(0, 0.5);
        this._siteUrlFrame.remove(this._urlEntry);
        this._siteUrlFrame.add(urlLabel);
        this._siteUrlFrame.show_all();

        this._siteAlertLabel.set_text(_("was added successfully"));
        this._siteAddButton.sensitive = false;
        this._switchAlertIcon(AlertIcon.HIDDEN);

        let newSite = this._weblinkListModel.createWeblink(url, title, 'browser');
        this._weblinkListModel.update();
        this._weblinkListModel.install(newSite);

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

    _onUrlEntryActivated: function() {
        if (!this._webView) {
            this._webView = new WebKit.WebView();
            this._webView.connect('load-changed', Lang.bind(this, this._onLoadChanged));
            this._webView.connect('load-failed', Lang.bind(this, this._onLoadFailed));
        }
        this._urlEntry.get_style_context().remove_class('url-entry-error');
        let url = this._urlEntry.get_text();
        this._webView.load_uri(url);
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
        this._siteAlertLabel.set_text(_("the address written does not exist or is not available"));
        this._switchAlertIcon(AlertIcon.ERROR);
        this._urlEntry.get_style_context().add_class('url-entry-error');
        return true;
    }
});
Builder.bindTemplateChildren(NewSiteBox.prototype);

const WeblinkListBoxRow = new Lang.Class({
    Name: 'WeblinkListBoxRow',
    Extends: Gtk.Bin,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-list-row.ui',
    templateChildren: [
        '_mainBox',
        '_icon',
        '_nameLabel',
        '_descriptionLabel',
        '_urlLabel',
        '_stateButton'
    ],

    _init: function(model, weblinkId) {
        this.parent();

        this._model = model;
        this._weblinkId = weblinkId;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);
        this._mainBox.show();

        this._stateButton.connect('clicked', Lang.bind(this, this._onStateButtonClicked));
    },

    get weblinkId() {
        return this._weblinkId;
    },

    set weblinkName(name) {
        if (!name) {
            name = _("Unknown weblink");
        }

        this._nameLabel.set_text(name);
    },

    set weblinkDescription(description) {
        if (!description) {
            description = '';
        }

        this._descriptionLabel.set_text(description);
    },

    set weblinkUrl(url) {
        if (!url) {
            url = '';
        }

        this._urlLabel.set_text(url);
    },

    set weblinkIcon(name) {
        if (!name) {
            name = 'gtk-missing-image';
        }

        this._icon.set_from_icon_name(name, Gtk.IconSize.DIALOG);
    },

    set weblinkState(state) {
        this._weblinkState = state;
        this._stateButton.hide();

        switch (this._weblinkState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._stateButton.set_label(_("UNINSTALL"));
                this._stateButton.show();
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._stateButton.set_label(_("INSTALL"));
                this._stateButton.show();
                break;

            default:
                break;
        }
    },

    _onStateButtonClicked: function() {
        switch (this._weblinkState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._model.uninstall(this._weblinkId);
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._model.install(this._weblinkId);
                break;
        }
    }
});
Builder.bindTemplateChildren(WeblinkListBoxRow.prototype);

const WeblinkListBox = new Lang.Class({
    Name: 'WeblinkListBox',
    Extends: PLib.ListBox,

    _init: function(model) {
        this.parent();

        this._model = model;
    }
});

const WeblinkFrame = new Lang.Class({
    Name: 'WeblinkFrame',
    Extends: Gtk.Frame,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-frame.ui',
    templateChildren: [
        '_mainBox',
        '_newSiteFrame',
        '_scrolledWindow',
        '_viewport'
    ],

    _init: function() {
        this.parent();
        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
        this.add(this._mainBox);
        this._mainBox.show_all();

        this._weblinkListModel = new AppListModel.WeblinkList();
        this._weblinkListModel.connect('changed', Lang.bind(this, this._onListModelChange));

        this._newSiteBox = new NewSiteBox(this._weblinkListModel);
        this._newSiteFrame.add(this._newSiteBox);
        this._listBox = new WeblinkListBox(this._weblinkListModel);
        this._viewport.add(this._listBox);
        this._listBox.show_all();
    },

    _onListModelChange: function(model, weblinks) {
        this._listBox.foreach(function(child) { child.destroy(); });

        weblinks.forEach(Lang.bind(this, function(item) {
            let row = new WeblinkListBoxRow(this._weblinkListModel, item);
            row.weblinkName = model.getName(item);
            row.weblinkDescription = model.getComment(item);
            row.weblinkUrl = model.getWeblinkUrl(item);
            row.weblinkIcon = model.getIcon(item);
            row.weblinkState = model.getState(item);

            this._listBox.add(row);
            row.show();
        }));
    },

    update: function() {
        this._weblinkListModel.update();
    }
});
Builder.bindTemplateChildren(WeblinkFrame.prototype);
