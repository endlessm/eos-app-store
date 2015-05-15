#!/usr/bin/env python3

import json

from os import path

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

    def trim_newer_full_updates(self, unfiltered_updates):
        buckets = {}
        for update in unfiltered_updates:
            bucket_name = self._build_app_bucket_name(update)
            # print(bucket_name)

            if bucket_name not in buckets:
                buckets[bucket_name] = []

            buckets[bucket_name].append(update)

        print("Assembled %s buckets of updates" % len(buckets.keys()))

        for bucket_name, updates in buckets.items():
            print(bucket_name)
            for update in updates:
                if update['isDiff']:
                    print(" ", "%s -> %s" % (update['fromVersion'], update['codeVersion']))
                else:
                    print(" ", update['codeVersion'])


        return unfiltered_updates

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
