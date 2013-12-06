// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Gtk = imports.gi.Gtk;
const Lang = imports.lang;

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
