import unittest

from startup.auto_updates.repo_chooser_launcher import EnvironmentManager,\
    RepoDef, EosInstallLauncher

#from eos_install_launcher import EnvironmentManager, RepoDef, EosInstallLauncher

class RepoChooserLauncherTestCase(unittest.TestCase):
    def setUp(self):
        self._test_object = EnvironmentManager()
           
    def test_when_given_demo_password_return_demo(self):
        repo_def = RepoDef("DEMO ", "http://apt.endlessm.com/demo/674078905c57ea21b9eb6fd8f45f5b5b9a49f912/installer.sh", "apt.endlessm.com/demo/25af78cc1e54ca5bca7e1dfe980d5a251930a432")
        self.assertEquals(repo_def.installer_url, self._test_object.find_repo(EnvironmentManager.DEMO_PASS).installer_url)
        
        self.assertEquals(repo_def.display, self._test_object.find_repo(EnvironmentManager.DEMO_PASS).display)
        self.assertEquals(repo_def.repo_url, self._test_object.find_repo(EnvironmentManager.DEMO_PASS).repo_url)

    def test_when_given_dev_password_return_dev(self):
        repo_def = RepoDef("DEV ", "http://em-vm-build/installer.sh", "em-vm-build/repository")
        self.assertEquals(repo_def.installer_url, self._test_object.find_repo(EnvironmentManager.DEV_PASS).installer_url)
        self.assertEquals(repo_def.display, self._test_object.find_repo(EnvironmentManager.DEV_PASS).display)
        self.assertEquals(repo_def.repo_url, self._test_object.find_repo(EnvironmentManager.DEV_PASS).repo_url)

    def test_when_given_codev_password_return_codev(self):
        repo_def = RepoDef("CO-DEV ", "http://em-codev-build1/installer.sh", "em-codev-build1/repository")
        self.assertEquals(repo_def.installer_url, self._test_object.find_repo(EnvironmentManager.CODEV_PASS).installer_url)
        self.assertEquals(repo_def.display, self._test_object.find_repo(EnvironmentManager.CODEV_PASS).display)
        self.assertEquals(repo_def.repo_url, self._test_object.find_repo(EnvironmentManager.CODEV_PASS).repo_url)

    def test_when_given_apt_testing_password_return_apt_testing(self):
        repo_def = RepoDef("APT TESTING ", "http://apt.endlessm.com/apt_testing/674078905c57ea21b9eb6fd8f45f5b5b9a49f912/installer.sh", "apt.endlessm.com/apt_testing/25af78cc1e54ca5bca7e1dfe980d5a251930a432")
        self.assertEquals(repo_def.installer_url, self._test_object.find_repo(EnvironmentManager.APT_TESTING_PASS).installer_url)
        self.assertEquals(repo_def.display, self._test_object.find_repo(EnvironmentManager.APT_TESTING_PASS).display)
        self.assertEquals(repo_def.repo_url, self._test_object.find_repo(EnvironmentManager.APT_TESTING_PASS).repo_url)
        
    def test_when_given_none_returns_prod(self):
        repo_def = RepoDef("", "http://apt.endlessm.com/updates/674078905c57ea21b9eb6fd8f45f5b5b9a49f912/installer.sh", "apt.endlessm.com/updates/25af78cc1e54ca5bca7e1dfe980d5a251930a432")
        self.assertEquals(repo_def.installer_url, self._test_object.find_repo(None).installer_url)
        self.assertEquals(repo_def.display, self._test_object.find_repo(None).display)
        self.assertEquals(repo_def.repo_url, self._test_object.find_repo(None).repo_url)
        
    def test_launcher_execute(self):
        output = "/bin/bash -c  'wget -q -O- http://foo.bar/installer.sh > /tmp/endless-installer.sh && bash /tmp/endless-installer.sh foo.bar/repo'"
        repo_def = RepoDef("", "http://foo.bar/installer.sh", "foo.bar/repo")
        
        launcher = EosInstallLauncher()
        
        self.assertEqual(output, launcher._apply_template(repo_def))
