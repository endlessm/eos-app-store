#!/usr/bin/env python3

class DeltaUpdatesTool(object):
    def parse_updates_json(self, location):
        pass

    def trim_newer_full_updates(self, unfiltered_updates):
        return unfiltered_updates

    def save_json(self, location, data):
        pass

    def trim(self):
        location = './updates.json'

        actual_updates = self.parse_updates_json(location)
        filtered_updates = self.trim_newer_full_updates(actual_updates)
        self.save_json(location, filtered_updates)

if __name__ == '__main__':
    DeltaUpdatesTool().trim()
