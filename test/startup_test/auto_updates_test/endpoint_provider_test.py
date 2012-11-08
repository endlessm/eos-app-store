import os
import shutil
import unittest

from startup.auto_updates import endpoint_provider

class EndpointProviderTestCase(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.expanduser("~/.endlessm"), True)

    def tearDown(self):
        shutil.rmtree(os.path.expanduser("~/.endlessm"), True)

    def test_if_endless_home_directory_already_exists_dont_blow_up(self):
        os.makedirs(os.path.expanduser("~/.endlessm"))

        endpoint_provider.get_endless_url()

        self.assertTrue(os.path.exists(os.path.expanduser("~/.endlessm/mirror")))

    def test_if_file_doesnt_exist_then_create_it(self):
        endpoint_provider.get_endless_url()

        self.assertTrue(os.path.exists(os.path.expanduser("~/.endlessm/mirror")))

    def test_if_no_file_exists_then_return_the_prod_url(self):
        self.assertEquals("http://apt.endlessdevelopment.com/updates", endpoint_provider.get_endless_url())

    def test_if_no_file_exists_create_it_with_the_prod_url(self):
        endpoint_provider.get_endless_url()

        with open(os.path.expanduser("~/.endlessm/mirror"), "r") as f:
            content = f.read()

        self.assertEquals("http://apt.endlessdevelopment.com/updates", content)

    def test_if_file_already_exists_return_with_given_content(self):
        existing_content = "this is the existing content"

        os.makedirs(os.path.expanduser("~/.endlessm"))
        with open(os.path.expanduser("~/.endlessm/mirror"), "w") as f:
            f.write(existing_content)

        self.assertEquals(existing_content, endpoint_provider.get_endless_url())

    def test_setting_the_url_writes_contents_to_the_file(self):
        expected_endpoint = "this is the new endpoint"

        endpoint_provider.set_endless_url(expected_endpoint)

        with open(os.path.expanduser("~/.endlessm/mirror"), "r") as f:
            actual_endpoint = f.read()

        self.assertEquals(expected_endpoint, actual_endpoint)

    def test_getting_the_url_returns_the_url_that_was_recently_set(self):
        expected_endpoint = "this is the new endpoint"

        endpoint_provider.set_endless_url(expected_endpoint)
        actual_endpoint = endpoint_provider.get_endless_url()

        self.assertEquals(expected_endpoint, actual_endpoint)

