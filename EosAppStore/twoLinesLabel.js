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

    vfunc_get_preferred_height_for_width: function(forWidth) {
        if (!this._keepSize) {
            let layout = this.get_layout();

            /* override the layout to force ellipsization */
            layout.set_ellipsize(Pango.EllipsizeMode.END);
            layout.set_width(forWidth * Pango.SCALE);

            /* we want two lines at most, and then ellipsize */
            layout.set_height(-2);

            let [w, h] = layout.get_pixel_size();

            return [w, h];
        }
        else {
            return this.parent(forWidth);
        }
    },

    vfunc_size_allocate: function(allocation) {
        if (!this._keepSize) {
            let layout = this.get_layout();

            /* same as get_preferred_height_for_width(), we override the
             * layout settings to force ellipsization after two lines of
             * text
             */
            layout.set_ellipsize(Pango.EllipsizeMode.END);
            layout.set_width(allocation.width * Pango.SCALE);
            layout.set_height(-2);

            /* override the passed allocation with the size of the layout,
             * if it's smaller than the allocated rectangle
             */
            let [w, h] = layout.get_pixel_size();
            let newAllocation = new Gtk.Allocation();
            newAllocation.x = allocation.x;
            newAllocation.y = allocation.y;
            newAllocation.width = w < allocation.width ? w : allocation.width;
            newAllocation.height = h < allocation.height ? h : allocation.height;
            this.parent(newAllocation);
        }
        else {
            this.parent(allocation);
        }
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
