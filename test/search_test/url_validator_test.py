import unittest

from search.url_validator import UrlValidator

class UrlValidatorTest(unittest.TestCase):
    def setUp(self):
        self._test_object = UrlValidator()

    def test_good_url(self):
        self.assertTrue(self._test_object.validate('http://www.google.com'))
        self.assertTrue(self._test_object.validate('www.google.com'))
        self.assertTrue(self._test_object.validate('google.com'))

    def test_url_with_whitespace_is_bad(self):
        self.assertFalse(self._test_object.validate('http:// foo.com'))
        self.assertFalse(self._test_object.validate('http://\tfoo.com'))
        self.assertFalse(self._test_object.validate('ht\ntp://foo.com'))

    def test_url_that_doesnt_contain_a_dot_is_bad(self):
        self.assertFalse(self._test_object.validate('www'))
        self.assertFalse(self._test_object.validate('google'))
        self.assertFalse(self._test_object.validate('yahoo_sucks'))

