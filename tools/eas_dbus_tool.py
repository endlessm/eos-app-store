#!/usr/bin/env python3

import sys
import re

import gi.repository
from gi.repository import Gio, GLib

MAIN_DEST = 'com.endlessm.AppStore'
MAIN_PATH = '/com/endlessm/AppStore'

INTROSPECTABLE_INTERFACE = 'org.freedesktop.DBus.Introspectable'

introspect_method = { "dest": MAIN_DEST,
                      "path": MAIN_PATH,
                      "interface": INTROSPECTABLE_INTERFACE,
                      "name": "Introspect",
                      "args": None,
                      "reply_format": GLib.VariantType.new ('(s)') }

# Most calls share some of these values
base_method = { "dest": MAIN_DEST,
                "path": MAIN_PATH,
                "interface": MAIN_DEST,
                "args": None,
                "reply_format": GLib.VariantType.new ('(b)') }

# Refresh
refresh_method_prototype = { "name": "Refresh" }
refresh_method = base_method.copy()
refresh_method.update(refresh_method_prototype)

# Uninstall
uninstall_method_prototype = { "name": "Uninstall" }
uninstall_method = base_method.copy()
uninstall_method.update(uninstall_method_prototype)

def uninstall_method_param_handler(method, params):
    print('Package: %s' % params[0])
    method["args"] = GLib.Variant('(s)', (params[0],))
uninstall_method['arg_handler'] = uninstall_method_param_handler

# Install
install_method_prototype = { "name": "Install" }
install_method = base_method.copy()
install_method.update(install_method_prototype)

def install_method_param_handler(method, params):
    print('Package: %s' % params[0])
    method["args"] = GLib.Variant('(s)', (params[0],))
install_method['arg_handler'] = install_method_param_handler

# Update
update_method_prototype = { "name": "Update",
                            "reply_format": GLib.VariantType.new ('(b)') }
update_method = base_method.copy()
update_method.update(update_method_prototype)

def update_method_param_handler(method, params):
    print('Package: %s' % params[0])
    method["args"] = GLib.Variant('(sb)', (params[0], True))
update_method['arg_handler'] = update_method_param_handler

# Installed
installed_method_prototype = { "name": "ListInstalled",
                               "reply_format": GLib.VariantType.new ('(as)') }
installed_method = base_method.copy()
installed_method.update(installed_method_prototype)

# Updatable
updatable_method_prototype = { "name": "ListUpdatable",
                               "reply_format": GLib.VariantType.new ('(as)') }
updatable_method = base_method.copy()
updatable_method.update(updatable_method_prototype)

# Removable
uninstallable_method_prototype = { "name": "ListUninstallable",
                                   "reply_format": GLib.VariantType.new ('(as)') }
uninstallable_method = base_method.copy()
uninstallable_method.update(uninstallable_method_prototype)

# List available
available_method_prototype = { "name": "ListAvailable",
                               "reply_format": GLib.VariantType.new ('(as)') }
available_method = base_method.copy()
available_method.update(available_method_prototype)

def available_method_param_post_handler(response, params):
    if len(params) != 1:
        return response

    print('Package grep: %s' % params[0])

    matching_packages = []
    for package in response:
        if re.search('.*%s.*' % params[0], package[0]):
            matching_packages.append(package)

    return matching_packages
available_method['arg_post_handler'] = available_method_param_post_handler

METHOD_MAP = {
    "refresh": refresh_method,
    "available": available_method,
    "installed": installed_method,
    "updatable": updatable_method,
    "uninstallable": uninstallable_method,
    "install": install_method,
    "update": update_method,
    "introspect": introspect_method,
    "uninstall": uninstall_method,
    # "visible": visible_property
}

if __name__ == '__main__':
    method_name = sys.argv[1]
    method = METHOD_MAP[method_name]
    print(method)

    if 'arg_handler' in method:
        method['arg_handler'](method, sys.argv[2:])

    bus   = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    reply = bus.call_sync(method['dest'],
                          method['path'],
                          method['interface'],
                          method['name'],
                          method['args'],
                          method['reply_format'],
                          Gio.DBusCallFlags.NONE,
                          -1,    # Timeout
                          None)  # Cancellable

    print()

    if reply == None:
        print("**ERROR. No return value!")
        exit(1)

    unpacked_reply = reply.unpack()
    print('Return arguments: %s' % len(unpacked_reply))

    for reply in unpacked_reply:
        print('-' * 40)
        response = reply

        if 'arg_post_handler' in method:
            response = method['arg_post_handler'](response, sys.argv[2:])

        try:
            object_iterator = iter(response)
            for list_item in object_iterator:
                print(list_item)
        except TypeError:
            print(response)
