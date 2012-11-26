import shutil
import os.path
import unittest
from startup.auto_updates.force_install_checker import ForceInstallChecker

class ForceInstallCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self._clean_up()
        os.makedirs(os.path.expanduser("~/.endlessm"))

        self._test_object = ForceInstallChecker()

    def tearDown(self):
        self._clean_up()

    def _clean_up(self):
        shutil.rmtree(os.path.expanduser("~/.endlessm"), True)

    def test_if_file_exists_then_should_restart(self):
        open(os.path.expanduser("~/.endlessm/needs_restart"), "w").close()   

        self.assertTrue(self._test_object.should_force_install())
        
    def test_if_file_doesnt_exists_then_should_not_restart(self):
        self.assertFalse(self._test_object.should_force_install())

    def test_if_reset_then_should_not_restart(self):
        open(os.path.expanduser("~/.endlessm/needs_restart"), "w").close()   

        self._test_object.install_accomplished()

        self.assertFalse(self._test_object.should_force_install())

    def test_resetting_when_there_is_no_file_doesnt_blow_up(self):
        self._test_object.install_accomplished()

        self.assertFalse(self._test_object.should_force_install())

    def test_need_to_do_install_creates_needs_restart_file(self):
        self._test_object.need_to_do_install()

        self.assertTrue(os.path.exists(os.path.expanduser("~/.endlessm/needs_restart")))

