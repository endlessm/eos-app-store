#!/usr/bin/env python3

import json

from os import path
from subprocess import call

class DeltaUpdatesTool(object):
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

        # print(app_id, arch, min_os_version, personality, locale)

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
        'Convert cmp= function to key= function'
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
        return sorted(updates, key=self.cmp_to_key(self._compare_code_versions))

    def _split_newer_updates(self, deltas):
        sorted_deltas = sorted(deltas, key=self.cmp_to_key(self._compare_from_versions))
        print("Sorted: ", len(sorted_deltas))

        if len(sorted_deltas) == 1:
            return [], sorted_deltas[-1]

        return sorted_deltas[:-2], sorted_deltas[-1]

    def trim_newer_full_updates(self, unfiltered_updates):
        filtered_updates = []

        # Split unfiltered updates into buckets of installable app
        # groupings
        buckets = {}
        for update in unfiltered_updates:
            bucket_name = self._build_app_bucket_name(update)
            # print(bucket_name)

            if bucket_name not in buckets:
                buckets[bucket_name] = []

            buckets[bucket_name].append(update)

        print("Assembled %s buckets of updates" % len(buckets.keys()))

        # Filter each bucketted update group
        for bucket_name, updates in buckets.items():
            print(bucket_name, len(updates))

            sorted_updates = self._sort_by_code_versions(updates)

            latest_version = sorted_updates[0]['codeVersion']
            # print('Latest: %s' % latest_version)

            latest_version_updates = [u for u in sorted_updates if u['codeVersion'] == latest_version]
            latest_version_diffs = [u for u in latest_version_updates if u['isDiff'] == True]

            if len(latest_version_diffs) > 0:
                # Split out the deltas to the newest version from others and remove them
                updates_to_delete, oldest_diff = self._split_newer_updates(latest_version_diffs)
                for update_to_delete in updates_to_delete:
                    print("Deleting delta %s version" % update_to_delete['fromVersion'])
                    sorted_updates.remove(update_to_delete)

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
                    # We may have duplicates so we need this check here
                    if deletable_update in sorted_updates:
                        sorted_updates.remove(deletable_update)
            else:
                # Since this is a script for testing updates, if we have none in a
                # bucket, then we don't need that bucket at all
                sorted_updates = []

            for update in sorted_updates:
                if update['isDiff']:
                    print(" ", "%s -> %s" % (update['fromVersion'], update['codeVersion']))
                else:
                    print(" ", update['codeVersion'])

            # Sanity check
            # assert len(sorted_updates) == 0 or len(sorted_updates) == 2, \
            #        "Resulting bucket results should always have either 0 or 2 results " \
            #        "(got: %s)" % len(sorted_updates)

            for update in sorted_updates:
                if update['isDiff']:
                    print(" ", "%s -> %s" % (update['fromVersion'], update['codeVersion']))
                else:
                    print(" ", update['codeVersion'])

            # Tack on the current filtered bucket to the output list
            filtered_updates += sorted_updates

        return filtered_updates

    def save_json(self, location, updates):
        with open(location, 'wt') as json_file:
            json.dump(updates, json_file, sort_keys = True, indent = 2,
                      separators=(',', ': '))

    def trim(self):
        location = './updates.json'
        output_location = './updates.new.json'

        actual_updates = self.parse_updates_json(location)
        filtered_updates = self.trim_newer_full_updates(actual_updates)
        self.save_json(output_location, filtered_updates)

if __name__ == '__main__':
    DeltaUpdatesTool().trim()
