import unittest
from mock import Mock #@UnresolvedImport

from startup.endless_updater import EndlessUpdater

class UpdateManagerTestCase(unittest.TestCase):
    def test_(self):
        test_object = EndlessUpdater()
        test_object.update()
