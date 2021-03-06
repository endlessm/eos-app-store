#!/usr/bin/env python3
# set expandtab ts=4 sw=4 ai

import json
import argparse

from os import path, utime
from shutil import move
from subprocess import call

class DeltaUpdatesTool(object):
    VERSION = '0.0.1'

    CACHE_PREFIX = '~/.cache/com.endlessm.AppStore/'
    DEFAULT_LOCATION = '%supdates.json' % CACHE_PREFIX
    META_RECORD_LOCATION = '%supdates_meta.json' % CACHE_PREFIX

    def __init__(self, target, no_meta_touch = False, debug = False,
                 verbose = False):
        self.debug = debug
        self.verbose = verbose
        self.target = path.expanduser(target)

        # Reversed the boolean since from the code standpoint we want
        # to know in the positive when to update the mtime
        self.touch_meta = not no_meta_touch

        if self.debug:
            print("Debug:", self.debug)

        if self.verbose:
            print("Verbose:", self.verbose)

        print("Target:", self.target)

    def parse_updates_json(self, location):
        if not path.exists(location):
            raise RuntimeError("File does not exist at %s" % location)

        data = None
        with open(location) as json_file:
            data = json.load(json_file)

        if not data:
            raise RuntimeError("No valid JSON data found in %s" % location)

        print("Found %d records in file" % len(data))

        return data

    def _build_app_bucket_name(self, update):
        app_id = update['appId']
        arch = update['arch']
        min_os_version = ".".join([str(update['minOsVersionObj']['major']),
                                   str(update['minOsVersionObj']['minor']),
                                   str(update['minOsVersionObj']['patch'])])

        locale = None
        try:
            locale = update['locale']
        except:
            pass

        personality = None
        try:
            personality = update['personality']
        except:
            pass

        if self.verbose:
            print(app_id, arch, min_os_version, personality, locale)

        bucket_name = "_".join([app_id, arch, min_os_version, personality or 'None',
                                locale or 'None'])

        return bucket_name

    def _compare_code_versions(self, a, b, cmp_func):
        return call('dpkg --compare-versions %s %s %s' % (a['codeVersion'],
                                                          cmp_func,
                                                          b['codeVersion']),
                    shell = True)

    def _compare_from_versions(self, a, b, cmp_func):
        return call('dpkg --compare-versions %s %s %s' % (a['fromVersion'],
                                                          cmp_func,
                                                          b['fromVersion']),
                    shell = True)

    def cmp_to_key(self, comparator):
        # Convert cmp= function to key= function
        class KeyComparator(object):
            def __init__(self, obj, *args):
                self.obj = obj
            def __lt__(self, other):
                return comparator(self.obj, other.obj, 'lt')
            def __gt__(self, other):
                return comparator(self.obj, other.obj, 'gt')
            def __eq__(self, other):
                return comparator(self.obj, other.obj, 'eq')
            def __le__(self, other):
                return comparator(self.obj, other.obj, 'lte')
            def __ge__(self, other):
                return comparator(self.obj, other.obj, 'gte')
            def __ne__(self, other):
                return comparator(self.obj, other.obj, 'ne')
        return KeyComparator

    def _sort_by_code_versions(self, updates):
        return sorted(updates, key = self.cmp_to_key(self._compare_code_versions))

    def _split_newer_updates(self, deltas, updates):
        sorted_deltas = sorted(deltas, key = self.cmp_to_key(self._compare_from_versions))
        if self.debug:
            print("Sorted:", len(sorted_deltas))

        # Find the farthest delta that has an actual full install candidate
        last_chainable_diff = None
        for sorted_update in reversed(sorted_deltas):
            if last_chainable_diff:
                break

            for candidate_update in updates:
                if candidate_update['isDiff'] == False and \
                   sorted_update['fromVersion'] == candidate_update['codeVersion']:
                    last_chainable_diff = sorted_update
                    break

        if last_chainable_diff:
            sorted_deltas.remove(last_chainable_diff)

        if len(sorted_deltas) == 1:
            return [], last_chainable_diff

        return sorted_deltas, last_chainable_diff

    def trim_newer_full_updates(self, unfiltered_updates):
        filtered_updates = []

        # Split unfiltered updates into buckets of installable app
        # groupings
        buckets = {}
        for update in unfiltered_updates:
            bucket_name = self._build_app_bucket_name(update)
            if self.verbose:
                print(bucket_name)

            if bucket_name not in buckets:
                buckets[bucket_name] = []

            buckets[bucket_name].append(update)

        if self.debug:
            print("Assembled %s buckets of updates" % len(buckets.keys()))

        # Filter each bucketted update group
        for bucket_name, updates in buckets.items():
            if self.debug:
                print(bucket_name, len(updates))

            sorted_updates = self._sort_by_code_versions(updates)

            latest_version = sorted_updates[0]['codeVersion']
            if self.debug:
                print('Latest: %s' % latest_version)

            latest_version_updates = [u for u in sorted_updates if u['codeVersion'] == latest_version]
            latest_version_diffs = [u for u in latest_version_updates if u['isDiff'] == True]

            if len(latest_version_diffs) > 0:
                # Split out the deltas to the newest version from others and remove them
                updates_to_delete, oldest_diff = self._split_newer_updates(latest_version_diffs, sorted_updates)
                for update_to_delete in updates_to_delete:
                    if self.verbose:
                        print("Deleting delta %s -> %s" % (update_to_delete['fromVersion'],
                                                           update_to_delete['codeVersion']))
                    sorted_updates.remove(update_to_delete)

                # If we don't have a good chain from update to diff, ignore this bucket
                if not oldest_diff:
                    continue

                updates_to_delete = []
                for update in sorted_updates:
                    # Remove all full bundles that are not the version from the largest version delta
                    if update['codeVersion'] != oldest_diff['fromVersion'] and update['isDiff'] == False:
                        updates_to_delete.append(update)

                    # Remove all deltas that don't target the latest version
                    if update['codeVersion'] != oldest_diff['codeVersion'] and update['isDiff'] == True:
                        updates_to_delete.append(update)

                    # Remove all deltas that aren't from the only full update
                    # XXX: Order of evalutation on this one is important since
                    #      only diffs have 'fromVersion' field
                    if update['isDiff'] == True and update['fromVersion'] != oldest_diff['fromVersion']:
                        updates_to_delete.append(update)

                for deletable_update in updates_to_delete:
                    if self.verbose:
                        if deletable_update['isDiff']:
                             print("D ", "%s -> %s" % (deletable_update['fromVersion'],
                                                       deletable_update['codeVersion']))
                        else:
                             print("D ", deletable_update['codeVersion'])

                    # We may have duplicates so we need this check here
                    if deletable_update in sorted_updates:
                        sorted_updates.remove(deletable_update)
            else:
                # Since this is a script for testing updates, if we have none in a
                # bucket, then we don't need that bucket at all
                sorted_updates = []

            # Sanity check
            assert len(sorted_updates) == 0 or len(sorted_updates) == 2, \
                   "Resulting bucket results should always have either 0 or 2 results " \
                   "(got: %s)" % len(sorted_updates)

            if self.debug:
                for update in sorted_updates:
                    if update['isDiff']:
                        print(" ", "%s -> %s" % (update['fromVersion'],
                                                 update['codeVersion']))
                    else:
                        print(" ", update['codeVersion'])

            # Tack on the current filtered bucket to the output list
            filtered_updates += sorted_updates

        return filtered_updates

    def save_json(self, location, updates):
        # Backup old version
        if path.exists(location):
            backup_filename = None
            for next_index in range(0, 100):
                path_to_try = "%s.json.%d.old" % (path.splitext(location)[0],
                                                  next_index)
                if not path.exists(path_to_try):
                    backup_filename = path_to_try
                    break

            if not backup_filename:
                raise RuntimeError("Could not find a file to save the backup to!")

            print("Backing up old file to %s" % backup_filename)
            move(location, backup_filename)

        # Save the new file
        with open(location, 'wt') as json_file:
            json.dump(updates, json_file, sort_keys = True, indent = 2,
                      separators = (',', ': '))

    def touch_meta_record(self, meta_record_location):
        location = path.expanduser(meta_record_location)
        if path.exists(location):
            utime(location, None)
        else:
            print("WARNING! Could not update time on the meta record!")

    def trim(self):
        if not path.exists(self.target):
            raise RuntimeError("File %s does not exists!" % self.target)

        actual_updates = self.parse_updates_json(self.target)

        filtered_updates = self.trim_newer_full_updates(actual_updates)
        print("Filtered records:", len(filtered_updates))

        self.save_json(self.target, filtered_updates)

        if self.touch_meta:
            self.touch_meta_record(self.META_RECORD_LOCATION)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Strips updates.json to bare minimum'
                                                   'to test update finctionality')

    parser.add_argument('target',
                        help = 'Use the following file as the target (default: %s)' % \
                               DeltaUpdatesTool.DEFAULT_LOCATION,
                        default = DeltaUpdatesTool.DEFAULT_LOCATION,
                        nargs = '?')

    parser.add_argument('--no-meta-touch',
            help = 'Don\'t try to update mtime of %s' % \
                   DeltaUpdatesTool.META_RECORD_LOCATION,
            action = 'store_true')

    parser.add_argument('--debug',
            help = 'Enable debugging output',
            action = 'store_true')

    parser.add_argument('--verbose',
            help = 'Enable extremely verbose debugging output',
            action = 'store_true')

    parser.add_argument('--version',
            action = 'version',
            version = '%(prog)s v' + DeltaUpdatesTool.VERSION)

    args = parser.parse_args()

    if 'help' in args and args.help:
        parser.print_help()
    else:
        DeltaUpdatesTool(args.target,
                         args.no_meta_touch,
                         args.debug,
                         args.verbose).trim()
