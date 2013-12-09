// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gtk = imports.gi.Gtk;
const Lang = imports.lang;

const TwoLinesLabel = new Lang.Class({
    Name: 'TwoLinesLabel',
    Extends: Gtk.Label,

    _init: function(params) {
	     this.parent(params);
	     this._keepSize = false;
    },

    get keepSize() {
	     return this._keepSize;
    },

    set keepSize(keep) {
	     this._keepSize = keep;
    },

    vfunc_size_allocate: function(allocation) {
	     if (!this._keepSize) {
	         let layout = this.get_layout();
	         layout.set_height(-2);
	         let [w, h] = layout.get_pixel_size();
	         this.set_size_request(w, h);
        }

	     return this.parent(allocation);
    },

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
