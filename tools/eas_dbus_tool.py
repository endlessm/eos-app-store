#!/usr/bin/env python3

import sys
import re
import argparse

import gi.repository
from gi.repository import Gio, GLib

# ---------------------- METHOD IMPLEMENTATIOS ----------------------
class GenericEasDbusMethod(object):
    MAIN_DEST = 'com.endlessm.AppStore'
    MAIN_PATH = '/com/endlessm/AppStore'

    def __init__(self, name, method_name, params):
        self.name = name
        self.method_name = method_name

        self.destination = self.MAIN_DEST
        self.path = self.MAIN_PATH
        self.interface = self.MAIN_DEST

        self.timeout = -1;

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

class IntrospectEasDbusMethod(GenericEasDbusMethod):
    INTROSPECTABLE_INTERFACE = 'org.freedesktop.DBus.Introspectable'

    def __init__(self, params):
        super().__init__("introspect", "Introspect", params);

        self.interface = self.INTROSPECTABLE_INTERFACE
        self.reply_format = GLib.VariantType.new('(s)')

    def arg_post_handler(self, response):
        strr = ""
        object_iterator = iter(response)
        for list_item in object_iterator:
            strr = strr + list_item

        print(strr)
        return ""

class ShowUiEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("show", "show", params);

        self.reply_format = GLib.VariantType.new ('()')

    def _arg_handler(self, args):
        self.args = GLib.Variant('(ub)', (0, True,))

class ShowPageEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("page", "showPage", params);

        self.reply_format = GLib.VariantType.new ('()')

    def _arg_handler(self, args):
        print('Page: %s' % args.page)
        self.args = GLib.Variant('(us)', (0, args.page.lower(),))

    def define_action_arguments(parser):
        parser.add_argument('page',
                            help='Open the app store to this page')

class HideUiEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("hide", "hide", params);

        self.reply_format = GLib.VariantType.new ('()')

    def _arg_handler(self, args):
        self.args = GLib.Variant('(u)', (0,))

class RefreshEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("refresh", "Refresh", params);

class UninstallEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("uninstall", "Uninstall", params);

    def _arg_handler(self, args):
        print('App ID: %s' % args.app_id)
        self.args = GLib.Variant('(s)', (args.app_id,))

    def define_action_arguments(parser):
        parser.add_argument('app_id',
                            help='App ID to uninstall')

class InstallEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("install", "Install", params);

        # Install is a much longer operation
        self.timeout = 20 * 60 * 1000;

    def _arg_handler(self, args):
        print('App ID: %s' % args.app_id)
        self.args = GLib.Variant('(s)', (args.app_id,))

    def define_action_arguments(parser):
        parser.add_argument('app_id',
                            help='App ID to install')

class UpdateEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("update", "Update", params);

    def _arg_handler(self, args):
        print('App ID: %s' % args.app_id)
        self.args = GLib.Variant('(s)', (args.app_id,))

    def define_action_arguments(parser):
        parser.add_argument('app_id',
                            help='App ID to update')

class InstalledEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("installed", "ListInstalled", params);

        self.reply_format = GLib.VariantType.new ('(as)')

class UpdatableEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("updatable", "ListUpdatable", params);

        self.reply_format = GLib.VariantType.new ('(as)')

class UninstallableEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("uninstallable", "ListUninstallable", params);

        self.reply_format = GLib.VariantType.new ('(as)')

class AvailableEasDbusMethod(GenericEasDbusMethod):
    def __init__(self, params):
        super().__init__("available", "ListAvailable", params);

        self.reply_format = GLib.VariantType.new ('(as)')

    # TODO: Handle regex matching on response
    # def available_method_param_post_handler(response, params):
    #     if len(params) != 1:
    #         return response
    #
    #     print('Package grep: %s' % params[0])
    #
    #     matching_packages = []
    #     for package in response:
    #         if re.search('.*%s.*' % params[0], package[0]):
    #             matching_packages.append(package)
    #
    #     return matching_packages

# ---------------------- MAIN INVOCATION CLASS ----------------------

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

    def output_response(self, method, reply):
        unpacked_reply = reply.unpack()
        print('Return arguments: %s' % len(unpacked_reply))

        for reply in unpacked_reply:
            print('-' * 40)
            response = method.arg_post_handler(reply)

            try:
                object_iterator = iter(response)
                for list_item in object_iterator:
                    print(list_item)
            except TypeError:
                print(response)
            pass

    def invoke(self, method_name, params):
        action_class = self.__class__.class_from_method(method_name)
        if not action_class:
            print("Error! No method specified!")
            exit(1)

        action = action_class(params)
        print("Invoking DBus method:", action.method_name)

        bus   = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        reply = bus.call_sync(action.destination,
                              action.path,
                              action.interface,
                              action.method_name,
                              action.args,
                              action.reply_format,
                              Gio.DBusCallFlags.NONE,
                              action.timeout,    # Timeout
                              None)              # Cancellable

        print()

        if reply == None:
            print("**ERROR. No return value!")
            exit(1)

        self.output_response(action, reply)

# ---------------------- CLI LOGIC ENTRY ----------------------
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
