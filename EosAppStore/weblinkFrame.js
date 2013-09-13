//: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gdk = imports.gi.Gdk;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const GObject = imports.gi.GObject;
const Gtk = imports.gi.Gtk;
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const PLib = imports.gi.PLib;
const WebKit = imports.gi.WebKit2;

const WeblinkListModel = imports.appListModel;
const Builder = imports.builder;
const Lang = imports.lang;
const Signals = imports.signals;

const NEW_SITE_TITLE_LIMIT = 20;
const NEW_SITE_DEFAULT_MESSAGE = "ex.: http://wwww.globoesporte.com";
const NEW_SITE_ADDED_MESSAGE = "was added successfully";
const NEW_SITE_SUCCESS_TIMEOUT = 3;
const NEW_SITE_UNAVAILABLE = "the address written does not exist or is not available";

const NewSiteAlertItem = {
    NOTHING: 0,
    SPINNER: 1,
    CANCEL: 2,
    ERROR: 3,
};

const NewSiteBox = new Lang.Class({
    Name: 'NewSiteBox',
    Extends: Gtk.Bin,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-new-site-frame.ui',
    templateChildren: [
	'_mainBox',
	'_siteIcon',
	'_siteEntry',
	'_siteAlertSpinner',
	'_siteAlertCancel',
	'_siteAlertIcon',
	'_siteAlertLabel',
	'_siteAddButton',
    ],

    _init: function(weblinkListModel) {
	this.parent();

	this.initTemplate({ templateRoot: '_mainBox',
			    bindChildren: true,
			    connectSignals: true });
	this.add(this._mainBox);
	this._mainBox.show_all();

	this._switchAlert(NewSiteAlertItem.NOTHING);

	this._weblinkListModel = weblinkListModel;
	this._newSiteError = false;
	this._webView = null;
    },

    _reset: function() {
	this._siteAddButton.visible = false;
	this._switchAlert(NewSiteAlertItem.NOTHING);
	this._siteAlertLabel.set_text(NEW_SITE_DEFAULT_MESSAGE);
	this._siteEntry.set_text("");
	this._siteEntry.max_length = 0;
	this._siteEntry.halign = Gtk.Align.FILL;
	this._siteEntry.grab_focus();
    },

    _showAlertSpinner: function(show) {
	if (show) {
	    this._siteAlertSpinner.opacity = 1;
	    this._siteAlertSpinner.start();
	} else {
	    this._siteAlertSpinner.stop();
	    this._siteAlertSpinner.opacity = 0;
	}
    },

    _switchAlert: function(newItem) {
	switch (newItem) {
	case NewSiteAlertItem.NOTHING:
	    this._showAlertSpinner(false);
	    this._siteAlertIcon.visible = false;
	    this._siteAlertCancel.visible = false;
	    break;
	case NewSiteAlertItem.SPINNER:
	    this._showAlertSpinner(true);
	    this._siteAlertIcon.visible = false;
	    this._siteAlertCancel.visible = false;
	    break;
	case NewSiteAlertItem.CANCEL:
	    this._showAlertSpinner(false);
	    this._siteAlertIcon.visible = false;
	    this._siteAlertCancel.visible = true;
	    break;
	case NewSiteAlertItem.ERROR:
	    this._showAlertSpinner(false);
	    this._siteAlertIcon.visible = true;
	    this._siteAlertCancel.visible = false;
	    break;
	}
    },

    _editSite: function() {
	this._switchAlert(NewSiteAlertItem.CANCEL);
	this._siteAddButton.visible = true;
	this._siteEntry.set_text(this._webView.get_title());
	this._siteAlertLabel.set_text(this._webView.get_uri());

	/* Narrow the entry and put the focus so user can change the title */
	let [entryWidth, entryHeight] = this._siteEntry.get_size_request();
	this._siteEntry.max_length = NEW_SITE_TITLE_LIMIT;
	this._siteEntry.halign = Gtk.Align.START;
    },

    _onEditSiteCancel: function() {
	this._reset();
    },


    _onSiteAdd: function() {
	let url = this._siteAlertLabel.get_text();
	let title = this._siteEntry.get_text();

	this._siteEntry.sensitive = false;
	this._siteAlertLabel.set_text(NEW_SITE_ADDED_MESSAGE);
	this._siteAddButton.sensitive = false;
	this._switchAlert(NewSiteAlertItem.NOTHING);

	let newSite = this._weblinkListModel.createWeblink(url, title, "browser");
	this._weblinkListModel.update();
	this._weblinkListModel.installWeblink(newSite);

	GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,
				 NEW_SITE_SUCCESS_TIMEOUT,
				 Lang.bind(this, function() {
				     this._siteEntry.sensitive = true;
				     this._siteAddButton.sensitive = true;
				     this._reset();
				     return false;
				 }));
    },

    _onSiteEntryActivated: function() {
	if (!this._webView) {
	    this._webView = new WebKit.WebView();
	    this._webView.connect('load-changed', Lang.bind(this, this._onLoadChanged));
	    this._webView.connect('load-failed', Lang.bind(this, this._onLoadFailed));
	}
	let url = this._siteEntry.get_text();
	this._webView.load_uri(url);
    },

    _onLoadChanged: function(webview, loadEvent) {
	switch (loadEvent) {
	case WebKit.LoadEvent.STARTED:
	    this._switchAlert(NewSiteAlertItem.SPINNER);
	    this._siteAlertLabel.set_text("searching");
	    this._newSiteError = false;
	    break;
	case WebKit.LoadEvent.FINISHED:
	    /* Error this was processed on "load-failed" handler*/
	    if (this._newSiteError) {
		return;
	    }

	    this._editSite();
	    break;
	}
    },

    _onLoadFailed: function() {
	this._newSiteError = true;
	this._siteAlertLabel.set_text(NEW_SITE_UNAVAILABLE);
	this._switchAlert(NewSiteAlertItem.ERROR);
	return true;
    },
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
        '_stateButton',
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
        if (!name)
            name = _("Unknown weblink");

        this._nameLabel.set_text(name);
    },

   set weblinkDescription(description) {
        if (!description)
            description = "";

        this._descriptionLabel.set_text(description);
    },

   set weblinkUrl(url) {
        if (!url)
            url = "";

        this._urlLabel.set_text(url);
    },

    set weblinkIcon(name) {
        if (!name)
            name = "gtk-missing-image";

        this._icon.set_from_icon_name(name, Gtk.IconSize.DIALOG);
    },

    set weblinkState(state) {
        this._weblinkState = state;
        this._stateButton.hide();

        switch (this._weblinkState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._stateButton.set_label(_('UNINSTALL'));
                this._stateButton.show();
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._stateButton.set_label(_('INSTALL'));
                this._stateButton.show();
                break;

            default:
                break;
        }
    },

    _onStateButtonClicked: function() {
        switch (this._weblinkState) {
            case EosAppStorePrivate.AppState.INSTALLED:
                this._model.uninstallWeblink(this._weblinkId);
                break;

            case EosAppStorePrivate.AppState.UNINSTALLED:
                this._model.installWeblink(this._weblinkId);
                break;
        }
    },
});
Builder.bindTemplateChildren(WeblinkListBoxRow.prototype);

const WeblinkListBox = new Lang.Class({
    Name: 'WeblinkListBox',
    Extends: PLib.ListBox,

    _init: function(model) {
        this.parent();

        this._model = model;
    },
});

const WeblinkDescriptionBox = new Lang.Class({
    Name: 'WeblinkDescriptionBox',
    Extends: Gtk.Frame,

    _init: function() {
        this.parent();
    },
});

const WeblinkFrame = new Lang.Class({
    Name: 'WeblinkFrame',
    Extends: Gtk.Frame,

    templateResource: '/com/endlessm/appstore/eos-app-store-weblink-frame.ui',
    templateChildren: [
        '_mainBox',
	'_newSiteFrame',
        '_scrolledWindow',
        '_viewport',
    ],

    _init: function() {
        this.parent();
        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
	this.add(this._mainBox);
	this._mainBox.show_all();

        this._weblinkListModel = new WeblinkListModel.WeblinkList();
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
            row.weblinkName = model.getWeblinkName(item);
            row.weblinkDescription = model.getWeblinkComment(item);
	    row.weblinkUrl = model.getWeblinkUrl(item);
            row.weblinkIcon = model.getWeblinkIcon(item);
            row.weblinkState = model.getWeblinkState(item);

            this._listBox.add(row);
            row.show();
        }));
    },

    update: function() {
        this._weblinkListModel.update();
    },
});
Builder.bindTemplateChildren(WeblinkFrame.prototype);
