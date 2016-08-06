# Endless App Center

The Endless App Center is the user-facing component used to install and remove
desktop weblinks and folders. In the past, it was also an application installer;
however, it has been replaced in this capacity by GNOME Software.

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

The app center provides an `eos-reset-desktop` tool that resets the desktop to
its default state.
