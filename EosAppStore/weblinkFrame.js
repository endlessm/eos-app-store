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

const NewSiteAlertItem = {
    NOTHING: 0,
    SPINNER: 1,
    CANCEL: 2,
    ERROR: 3,
};

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
	'_newSiteBox',
	'_newSiteIcon',
	'_newSiteUrl',
	'_newSiteAlertSpinner',
	'_newSiteAlertCancel',
	'_newSiteAlertError',
	'_newSiteAlertLabel',
	'_newSiteAddButton',
	'_newSiteAddButtonImage',
	'_listFrame',
        '_scrolledWindow',
        '_viewport',
    ],

    _init: function() {
        this.parent();
	this._webkit = null;
	this._newSiteError = false;

        this.initTemplate({ templateRoot: '_mainBox', bindChildren: true, connectSignals: true, });
	this.add(this._mainBox);
	this._mainBox.show_all();

        this._weblinkListModel = new WeblinkListModel.WeblinkList();
        this._weblinkListModel.connect('changed', Lang.bind(this, this._onListModelChange));

        this._listBox = new WeblinkListBox(this._weblinkListModel);
        this._viewport.add(this._listBox);
        this._listBox.show_all();

	this._newSiteAlertSwitch(NewSiteAlertItem.NOTHING);
    },

    _setVisibleNewSiteAlertSpinner: function(isVisible) {
	if (isVisible) {
	    this._newSiteAlertSpinner.opacity = 1;
	    this._newSiteAlertSpinner.start();
	} else {
	    this._newSiteAlertSpinner.stop();
	    this._newSiteAlertSpinner.opacity = 0;
	}
    },

    _newSiteAlertSwitch: function(newItem) {
	switch (newItem) {
	case NewSiteAlertItem.NOTHING:
	    this._setVisibleNewSiteAlertSpinner(false);
	    this._newSiteAlertError.visible = false;
	    this._newSiteAlertCancel.visible = false;
	    break;
	case NewSiteAlertItem.SPINNER:
	    this._setVisibleNewSiteAlertSpinner(true);
	    this._newSiteAlertError.visible = false;
	    this._newSiteAlertCancel.visible = false;
	    break;
	case NewSiteAlertItem.CANCEL:
	    this._setVisibleNewSiteAlertSpinner(false);
	    this._newSiteAlertError.visible = false;
	    this._newSiteAlertCancel.visible = true;
	    break;
	case NewSiteAlertItem.ERROR:
	    this._setVisibleNewSiteAlertSpinner(false);
	    this._newSiteAlertError.visible = true;
	    this._newSiteAlertCancel.visible = false;
	    break;
	}
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

    _onNewSiteUrlActivated: function() {
	if (!this._webview) {
	    this._webview = new WebKit.WebView();
	    this._webview.connect('load-changed', Lang.bind(this, this._onUriLoadChanged));
	    this._webview.connect('load-failed', Lang.bind(this, this._onUriLoadFailed));
	}
	let url = this._newSiteUrl.get_text();
	this._webview.load_uri(url);
    },

    _onUriLoadChanged: function(webview, loadEvent) {
	switch (loadEvent) {
	case WebKit.LoadEvent.STARTED:
	    this._newSiteAlertSwitch(NewSiteAlertItem.SPINNER);
	    this._newSiteAlertLabel.set_text("searching");
	    this._newSiteError = false;
	    break;
	case WebKit.LoadEvent.FINISHED:
	    if (this._newSiteError) {
		return;
	    }

	    this._newSiteAlertSwitch(NewSiteAlertItem.CANCEL);
	    this._newSiteAddButton.visible = true;
	    this._newSiteUrl.set_text(webview.get_title());
	    this._newSiteAlertLabel.set_text(webview.get_uri());

	    /* Narrow the entry and put the focus so user can change the title */
	    let [entryWidth, entryHeight] = this._newSiteUrl.get_size_request();
	    this._newSiteUrl.max_length = NEW_SITE_TITLE_LIMIT;
	    this._newSiteUrl.halign = Gtk.Align.START;
	    break;
	default:
	    break;
	}
    },

    _onUriLoadFailed: function() {
	this._newSiteError = true;
	this._newSiteAlertLabel.set_text("the address written does not exist or is not available");
	this._newSiteAlertSwitch(NewSiteAlertItem.ERROR);
	return true;
    },

    _onNewSiteCancel: function() {
	this._newSiteReset();
    },

    _onNewSiteAdd: function() {
	let url = this._newSiteAlertLabel.get_text();
	let title = this._newSiteUrl.get_text();
	this._newSiteUrl.sensitive = false;
	this._newSiteAlertSwitch(NewSiteAlertItem.NOTHING);
	this._newSiteAlertLabel.set_text(NEW_SITE_ADDED_MESSAGE);
	this._newSiteAddButton.sensitive = false;
	let newSite = this._weblinkListModel.createWeblink(url, title, "browser");
	this.update();
	this._weblinkListModel.installWeblink(newSite);
	GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,
				 NEW_SITE_SUCCESS_TIMEOUT,
				 Lang.bind(this, function() {
				     this._newSiteUrl.sensitive = true;
				     this._newSiteAddButton.sensitive = true;
				     this._newSiteReset();
				     return false;
				 }));
    },

    _newSiteReset: function() {
	this._newSiteAddButton.visible = false;
	this._newSiteAlertSwitch(NewSiteAlertItem.NOTHING);
	this._newSiteAlertLabel.set_text(NEW_SITE_DEFAULT_MESSAGE);
	this._newSiteUrl.set_text("");
	this._newSiteUrl.max_length = 0;
	this._newSiteUrl.halign = Gtk.Align.FILL;
	this._newSiteUrl.grab_focus();
    },

    _getPixbufFromSurface: function(surface) {
	if (!surface) {
	    return null;
	}

	let surface_width = surface.get_width();
	let surface_height = surface.get_height();
	pixbuf = GdkPixbuf.get_from_surface(surface, 0, 0, surface_width, surface_height);
	if (surface_width != width || surface_height != height) {
	    pixbuf = pixbuf.scale_simple (width, height, Gdk.Interp.BILINEAR);
	}

	return pixbuf;
    },

    update: function() {
        this._weblinkListModel.update();
    },
});
Builder.bindTemplateChildren(WeblinkFrame.prototype);
