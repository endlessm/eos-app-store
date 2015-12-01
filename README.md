# Endless App Center

The Endless App Center is the user-facing component used to install, update,
and remove applications in the Endless OS.

## Building and installing

In order to build the app center on Endless OS you should use:

  $ ./autogen.sh \
  	--prefix /usr \
	--sysconfdir /etc \
	--libexecdir /usr/bin \
	--localstatedir /var
  $ make
  $ sudo make install

The various configuration options ensure that the files are installed in
the expected locations, and that the app center uses the expected paths when
checking system configuration and downloading files.

## Design

The app center is split in three parts:

 * the app manager system daemon
 * a backend library
 * the GUI

### App manager daemon

The app manager system daemon (`eam`) is hosted in a separate
[repository][eam] and is responsible for manipulating the file system when
installing, updating, and removing applications. The app center uses DBus
to communicate with the app manager.

### Backend library

The backend library is used to implement low level operations, from the
remote procedure calls to the app manager to downloading data from the app
server; it also implements the global model object which holds all the
available applications metadata; and it implements some of the widgets used
by the GUI layer for efficiency.

### GUI

The GUI layer glues together the backend library with the user-facing UI,
and it's responsible for handling the main application window.

## Developing and debugging

The app center is considered a system level component. As such, it's
activated via DBus from the shell whenever needed, instead of launched like
a common application. The app center is also automatically terminated after
a certain delay when the user is not interacting with it.

### Environment variables

There are various environment variables used to simplify the development of
the app center.

  * `EOS_APP_STORE_PERSIST=1` - Setting to a non-zero value will keep the
    app center in memory even when not visible.
  * `EOS_APP_STORE_WIDTH=px` - Setting to a positive value will disable the
    automatic resizing based on the screen width, and instead use the `px`
    value used in the variable.
  * `EOS_APP_STORE_DEBUG_WINDOW=1`- Setting to a non-zero value will keep
    the app center as a floating top-level window.
  * `EAS_TESTING=1` - Setting to 1 will redirect errors to stderr instead
    of using the journal.
  * `EAS_DEBUG_JOURNAL=1` - Setting to 1 will redirect all debugging
    messages to the journal.

### Tools

The app center provides small utilities aimed at QA and development.

  * `eos-fill-desktop` - Adds all installed applications to the desktop
  * `eos-reset-desktop` - Resets the desktop to its default state
  * `eos-reset-app-store` - Resets the various cached state and ensures
    that the app center is restarted

[eam]: https://github.com/endlessm/eos-app-manager
