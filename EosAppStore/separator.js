const Gtk = imports.gi.Gtk;

const Lang = imports.lang;

const EDGE_WIDTH = 55;
const SHADOW_HEIGHT = 11;

const FrameSeparator = new Lang.Class({
    Name: 'FrameSeparator',
    Extends: Gtk.Box,

    _init: function() {
        this.parent({ orientation: Gtk.Orientation.VERTICAL,
                      margin_top: 10 });

        this._separator = new Gtk.Separator({ orientation: Gtk.Orientation.HORIZONTAL });
        this._separator.get_style_context().add_class('frame-separator');
        this.add(this._separator);

        let shadows = new Gtk.Box({ orientation: Gtk.Orientation.HORIZONTAL });
        shadows.get_style_context().add_class('frame-separator-shadows');
        this.add(shadows);

        this._leftEdge = new Gtk.Frame({ width_request: EDGE_WIDTH,
                                         height_request: SHADOW_HEIGHT });
        this._leftEdge.get_style_context().add_class('left-edge');
        shadows.add(this._leftEdge);

        this._centerLine = new Gtk.Frame({ hexpand: true,
                                           height_request: SHADOW_HEIGHT });
        this._centerLine.get_style_context().add_class('center-line');
        shadows.add(this._centerLine);

        this._rightEdge = new Gtk.Frame({ width_request: EDGE_WIDTH,
                                         height_request: SHADOW_HEIGHT });
        this._rightEdge.get_style_context().add_class('right-edge');
        shadows.add(this._rightEdge);

        this.show_all();
    }
});
