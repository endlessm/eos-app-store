import uuid

class Shortcuts():
    def __init__(self, array=None):
        self._array = []
        self._copy_array(array)

    def _copy_array(self, array):
        if array:
            for item in array:
                self.append(item)

    def __getitem__(self, key):
        return self._array[key]

    def __delitem__(self, key):
        del self._array[key]

    def __setitem__(self, key, value):
        self._array[key] = self._scrub_uuid(value)

    def __eq__(self, other):
        if isinstance(other, Shortcuts):
            return self._array == other._array
        return self._array == other

    def append(self, item):
        self._array.append(self._scrub_uuid(item))

    def _scrub_uuid(self, item):
        if hasattr(item,"uuid") and item.uuid() is None:
            item.set_uuid(uuid.uuid1().hex)
        return item

    def remove(self, item):
        return self._array.remove(item)

    def index(self, item):
        return self._array.index(item)

    def __len__(self):
        return len(self._array)

    def insert(self, index, item):
        self._array.insert(index, item)

