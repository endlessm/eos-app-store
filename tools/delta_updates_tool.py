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

    def trim_newer_full_updates(self, unfiltered_updates):
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
