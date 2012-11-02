import unittest
from mock import Mock #@UnresolvedImport

from startup.auto_updates.install_notifier_presenter import InstallNotifierPresenter

class InstallNotifierPresenterTestCase(unittest.TestCase):
    def setUp(self):
        self._mock_view = Mock()
        self._mock_model = Mock()
    
    def test_(self):
        self._mock_view.display = Mock()
        
        InstallNotifierPresenter(self._mock_view, self._mock_model)
        
        self._mock_view.display.assert_called_once_with()