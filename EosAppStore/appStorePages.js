const Gio = imports.gi.Gio;
const Gtk = imports.gi.Gtk;
const Lang = imports.lang;
const Signals = imports.signals;

var AppStorePageManager = new Lang.Class({
    Name: 'AppStorePageManager',
    Extends: Gtk.Stack,

    _init: function() {
        this._providers = {};
        this.parent({ visible: true });

        this.connect('notify::visible-child-name', Lang.bind(this, this._onPageChanged));
    },

    _onPageChanged: function() {
        let page = this.visible_child;
        if (page) {
            page.populate();
        }
    },

    _ensurePage: function(pageId) {
        let page = this.get_child_by_name(pageId);
        if (page) {
            return page;
        }

        let provider = this._providers[pageId];
        if (!provider) {
            return null;
        }

        page = provider.createPage(pageId);
        this.add_named(page, pageId);

        this.child_set_property(page, 'title', page.getName());
        this.child_set_property(page, 'icon-name', page.getIcon());

        return page;
    },

    registerProvider: function(provider) {
        let pageIds = provider.getPageIds();
        pageIds.forEach(Lang.bind(this, function(pageId) {
            this._providers[pageId] = provider;
            this._ensurePage(pageId);
        }));
    },

    showPage: function(pageId) {
        this.visible_child_name = pageId;
    }
});

var AppStorePageProvider = new Lang.Interface({
    Name: 'AppStorePageProvider',

    createPage: Lang.Interface.UNIMPLEMENTED,
    getPageIds: Lang.Interface.UNIMPLEMENTED
});
Signals.addSignalMethods(AppStorePageProvider.prototype);
