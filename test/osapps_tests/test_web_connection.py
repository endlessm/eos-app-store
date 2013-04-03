import unittest
from osapps.web_connection import WebConnection

class WebConnectionTestCase(unittest.TestCase):
    def test_getting_data_from_a_website(self):
        content = WebConnection().get("http://www.google.com")
        
        self.assertTrue("</html>" in content)
        
    def test_getting_data_from_a_website_with_basic_auth(self):
        content = WebConnection().get("http://apt.endlessdevelopment.com/updates/install/version.json", "endlessos", "install")
        
        self.assertTrue("version" in content)
        
    def test_getting_data_from_a_website_with_redirect_and_basic_auth(self):
        content = WebConnection().get("http://apt.endlessm.com/updates/install/version.json", "endlessos", "install")
        
        self.assertTrue("version" in content)        
        
    def test_404_errors_are_handled_well(self):
        url = "http://www.asolutions.com/asdfasdfasdfasdfasdfasdfasdfasdf"
        
        try:
            WebConnection().get(url)
            self.fail("Should have thrown an exception")
        except(Exception) as e:
            self.assertEquals("Could not access url (" + url + "): Not Found", e.message)

    def test_bad_url(self):
        url = "asdfasdfasdfasdfasdfasdfasdfasdf"
        
        try:
            WebConnection().get(url)
            self.fail("Should have thrown an exception")
        except(Exception) as e:
            self.assertEquals("Could not access url (" + url + "): unknown url type: " + url, e.message)
