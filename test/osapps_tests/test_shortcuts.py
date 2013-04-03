from unittest import TestCase
from osapps.shortcuts import Shortcuts
from osapps.app_shortcut import AppShortcut

class ShortcutsTest(TestCase):

    def setup(self):
        pass

    def test_get_item_at_location(self):
        test_data = ["foo","bar","foobar"]
        shortcuts = Shortcuts(test_data) 

        self.assertEquals("bar", shortcuts[1])

    def test_insert_item(self):
        shortcuts = Shortcuts() 

        shortcuts.append("foo")
        shortcuts.append("foobar")

        shortcuts.insert(1, "bar")

        self.assertEquals(["foo","bar","foobar"], shortcuts)
        self.assertEquals(Shortcuts(["foo","bar","foobar"]), shortcuts)

    def test_remove_item(self):
        shortcuts = Shortcuts() 

        shortcuts.append("foo")
        shortcuts.append("bar")
        shortcuts.append("foobar")

        shortcuts.remove("bar")

        self.assertEquals(["foo","foobar"], shortcuts)
        self.assertEquals(Shortcuts(["foo","foobar"]), shortcuts)

    def test_del_item_at_location(self):
        test_data = ["foo","bar","foobar"]
        shortcuts = Shortcuts(test_data) 

        del shortcuts[1]

        self.assertEquals(["foo","foobar"], shortcuts)
        self.assertEquals(Shortcuts(["foo","foobar"]), shortcuts)

    def test_set_item_at_location(self):
        shortcuts = Shortcuts(["something"])

        shortcuts[0] = "foo"

        self.assertEquals("foo", shortcuts[0])

    def test_set_item_sets_uuid_when_app_shortcut_set(self):
        shortcuts = Shortcuts([AppShortcut("","","")])

        new_shortcut = AppShortcut("","","")
        shortcuts[0] = new_shortcut

        self.assertTrue(shortcuts[0].uuid() is not None)

    def test_array_equality(self):
        shortcuts = Shortcuts()

        self.assertEquals([], shortcuts)
    
    def test_set_item_does_not_set_uuid_when_app_shortcut_set_and_uuid_not_empty(self):
        shortcuts = Shortcuts([AppShortcut("","","")])

        new_shortcut = AppShortcut("","","",[],"uuid")
        shortcuts[0] = new_shortcut

        self.assertEquals("uuid", shortcuts[0].uuid())

    def test_append_item(self):
        shortcuts = Shortcuts()

        shortcuts.append("foo")

        self.assertEquals(["foo"], shortcuts)

    def test_append_item(self):
        shortcuts = Shortcuts()

        shortcuts.append("foo")
        shortcuts.append("bar")
        shortcuts.append("baz")

        self.assertEquals(3, len(shortcuts))

    def test_set_uuid_when_app_shortcut_appended(self):
        shortcuts = Shortcuts()

        shortcut = AppShortcut("","","")
        shortcuts.append(shortcut)

        self.assertTrue(shortcuts[0].uuid() is not None)

    def test_do_notset_uuid_when_app_shortcut_appended_and_uuid_not_empty(self):
        shortcuts = Shortcuts()

        shortcut = AppShortcut("","","", [], "uuid")
        shortcuts.append(shortcut)

        self.assertEquals("uuid", shortcuts[0].uuid())

    def test_iterate(self):
        test_data = ["foo","bar","foobar"]
        shortcuts = Shortcuts(test_data) 

        actual = []

        for item in shortcuts:
            actual.append(item)

        self.assertEquals(actual, test_data)

    def test_item_index(self):
        item1 = "foo"
        item2 = "bar"
        item3 = "baz"
        shortcuts = Shortcuts([item2, item1, item3])

        self.assertEquals(0, shortcuts.index(item2))
        self.assertEquals(1, shortcuts.index(item1))
        self.assertEquals(2, shortcuts.index(item3))



