#!/usr/bin/env python3

import sys
import re
import argparse

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
    "available": available_method,
    "installed": installed_method,
    "updatable": updatable_method,
    "uninstallable": uninstallable_method,
    "introspect": introspect_method,
}

class GenericEasDbusMethod(object):
    def __init__(self, name, method_name, params):
        self.name = name
        self.method_name = method_name

        self.destination = MAIN_DEST
        self.path = MAIN_PATH
        self.interface = MAIN_DEST

        self.args = None
        self.reply_format = GLib.VariantType.new ('(b)')

        self.params = params

        self.arg_handler(params)

    def arg_handler(self, params):
        if params != None:
            self._arg_handler(params)

    def _arg_handler(self, params):
        pass

    def arg_post_handler(self, response):
        return response

    def define_action_arguments(parser):
        pass

class RefreshEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("refresh", "Refresh", params);

class UninstallEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("uninstall", "Uninstall", params);

    def _arg_handler(self, args):
        print('Package: %s' % args.app_id)
        self.args = GLib.Variant('(s)', (args.app_id,))

    def define_action_arguments(parser):
        parser.add_argument('app_id',
                            help='App ID to uninstall')

class InstallEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("install", "Install", params);

    def _arg_handler(self, args):
        print('Package: %s' % args.app_id)
        self.args = GLib.Variant('(s)', (args.app_id,))

    def define_action_arguments(parser):
        parser.add_argument('app_id',
                            help='App ID to install')

class UpdateEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("update", "Update", params);

    def _arg_handler(self, args):
        print('Package: %s' % args.app_id)
        self.args = GLib.Variant('(s)', (args.app_id,))

    def define_action_arguments(parser):
        parser.add_argument('app_id',
                            help='App ID to update')

class EasDbusTool(object):
    VERSION = '0.1'

    @staticmethod
    def attach_parsers(parser):
        subparsers = parser.add_subparsers(dest='action')

        for subclass in GenericEasDbusMethod.__subclasses__():
            subclass_instance = subclass(None)
            # print("Attaching module: " + subclass_instance.name)

            subparser = subparsers.add_parser(subclass_instance.name)
            subclass.define_action_arguments(subparser)

    @staticmethod
    def class_from_method(method):
        for subclass in GenericEasDbusMethod.__subclasses__():
            subclass_instance = subclass(None)
            if subclass_instance.name == method:
                return subclass

        return None

    def __init__(self, debug = False, verbose = False):
        pass

    def invoke(self, method_name, params):
        method_class = self.__class__.class_from_method(method_name)
        if not method_class:
            print("Error! No method specified!")
            exit(1)

        method = method_class(params)
        print(method.name)

        bus   = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        reply = bus.call_sync(method.destination,
                              method.path,
                              method.interface,
                              method.method_name,
                              method.args,
                              method.reply_format,
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

            response = method.arg_post_handler(response)

            try:
                object_iterator = iter(response)
                for list_item in object_iterator:
                    print(list_item)
            except TypeError:
                print(response)
            pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'App store DBus test tool')

    EasDbusTool.attach_parsers(parser)

    parser.add_argument('--debug',
            help = 'Enable debugging output',
            action = 'store_true')

    parser.add_argument('--verbose',
            help = 'Enable extremely verbose debugging output',
            action = 'store_true')

    parser.add_argument('--version',
            action = 'version',
            version = '%(prog)s v' + EasDbusTool.VERSION)

    args = parser.parse_args()

    method = args.action

    if ('help' in args and args.help) or not args.action:
        parser.print_help()
    else:
        EasDbusTool(args.debug, args.verbose).invoke(args.action, args)
