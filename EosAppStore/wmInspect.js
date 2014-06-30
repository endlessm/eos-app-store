const Lang = imports.lang;
const Signals = imports.signals;
const Wnck = imports.gi.Wnck;

const WMInspect = new Lang.Class({
    Name: 'WMInspect',

    _init: function() {
        this._firstSignal = true;
        this._screen = Wnck.Screen.get_default();
        this._screen.connect('active-window-changed', Lang.bind(this,
            this._onActiveWindowChanged));
    },

    _onActiveWindowChanged: function() {
        let activeWindow = this._screen.get_active_window();

        if (!activeWindow)
            return;

	// See #2518. Wnck.Screen always sends the current active window, but we
	// are interested in when the active window changes, not what is the
	// current active window. So let's ignore this first advertisement.
        if (this._firstSignal) {
	    this._firstSignal = false;
            return;
        }

        this.emit('active-window-changed', activeWindow);
    }
});
Signals.addSignalMethods(WMInspect.prototype);
