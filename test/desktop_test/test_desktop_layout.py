import unittest
from mock import Mock

from desktop.desktop_layout import DesktopLayout

class DesktopLayoutTest(unittest.TestCase):
    def test_(self):
        w1 = Mock()
        w2 = Mock()
        w3 = Mock()

        w1.allocation = Mock(return_value=10)
        w2.allocation = Mock(return_value=20)
        w3.allocation = Mock(return_value=30)

        w1.allocation.height = 10
        w2.allocation.height = 20
        w3.allocation.height = 30

        self.assertEquals(10, DesktopLayout.calculate_total_top_padding(w1, w2, w3))

