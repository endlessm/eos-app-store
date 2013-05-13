from mock import Mock
import unittest
from eos_util.image import Image
from gi.repository import Gdk
from gi.repository import GdkPixbuf

class TestImage(unittest.TestCase):
    def setUp(self):
        self.pixbuf = Mock()
        self.test_object = Image(self.pixbuf)

    def test_draw(self):
        draw_method = Mock()

        self.test_object.draw(draw_method)

        draw_method.assert_called_once_with(self.pixbuf)

    def test_draw_centered(self):
        draw_method = Mock()
        x = 10
        y = 20
        w = 30
        h = 40
        width = 5
        height = 6
        self.pixbuf.get_width = Mock(return_value = width)
        self.pixbuf.get_height = Mock(return_value = height)
        x_new = x + (w - width) / 2
        y_new = y + (h - height) / 2

        self.test_object.draw_centered(draw_method, x, y, w, h)

        draw_method.assert_called_once_with(self.pixbuf, x_new, y_new)
        
    def test_scale(self):
        scaled_pixbuf = Mock()
        self.pixbuf.scale_simple = Mock(return_value = scaled_pixbuf)
        width = Mock()
        height = Mock()

        self.test_object.scale(width, height)

        self.assertEquals(self.test_object._pixbuf, scaled_pixbuf)

        self.pixbuf.scale_simple.assert_called_once_with(width, height, GdkPixbuf.InterpType.BILINEAR)
    

    def test_scale_from_width(self):
        scaled_pixbuf = Mock()
        self.pixbuf.get_width = Mock(return_value = 5)
        self.pixbuf.get_height = Mock(return_value = 6)
        self.pixbuf.scale_simple = Mock(return_value = scaled_pixbuf)
        width = 10

        self.test_object.scale_from_width(width)

        self.assertEquals(self.test_object._pixbuf, scaled_pixbuf)

        self.pixbuf.scale_simple.assert_called_once_with(width, 12, GdkPixbuf.InterpType.BILINEAR)
    
    def test_scale_from_height(self):
        scaled_pixbuf = Mock()
        self.pixbuf.get_width = Mock(return_value = 6)
        self.pixbuf.get_height = Mock(return_value = 5)
        self.pixbuf.scale_simple = Mock(return_value = scaled_pixbuf)
        height = 10

        self.test_object.scale_from_height(height)

        self.assertEquals(self.test_object._pixbuf, scaled_pixbuf)

        self.pixbuf.scale_simple.assert_called_once_with(12, height, GdkPixbuf.InterpType.BILINEAR)

    def test_scale_to_best_fit_for_landscape_image_smaller_than_screen(self):
        self.pixbuf.get_width = Mock(return_value=450)
        self.pixbuf.get_height = Mock(return_value=200)
        self.test_object.scale = Mock()
        self.test_object.scale_to_best_fit(500, 400)
        self.test_object.scale.assert_called_once_with(900, 400)
        
    def test_scale_to_best_fit_for_landscape_image_larger_than_screen(self):
        self.pixbuf.get_width = Mock(return_value=800)
        self.pixbuf.get_height = Mock(return_value=200)
        self.test_object.scale = Mock()
        self.test_object.scale_to_best_fit(500, 400)
        self.test_object.scale.assert_called_once_with(1600, 400)

    def test_scale_to_best_fit_for_portrait_image_smaller_than_screen(self):
        self.pixbuf.get_width = Mock(return_value=200)
        self.pixbuf.get_height = Mock(return_value=350)
        self.test_object.scale = Mock()
        self.test_object.scale_to_best_fit(500, 400)
        self.test_object.scale.assert_called_once_with(500, 875)
        
    def test_scale_to_best_fit_for_portrait_image_larger_than_screen(self):
        self.pixbuf.get_width = Mock(return_value=450)
        self.pixbuf.get_height = Mock(return_value=800)
        self.test_object.scale = Mock()
        self.test_object.scale_to_best_fit(500, 400)
        self.test_object.scale.assert_called_once_with(500, 888)

    def test_stretch_horizontal(self):
        scaled_pixbuf = Mock()
        self.pixbuf.get_height = Mock(return_value = 6)
        self.pixbuf.scale_simple = Mock(return_value = scaled_pixbuf)
        width = 10

        self.test_object.stretch_horizontal(width)

        self.assertEquals(self.test_object._pixbuf, scaled_pixbuf)

        self.pixbuf.scale_simple.assert_called_once_with(width, 6, GdkPixbuf.InterpType.BILINEAR)

