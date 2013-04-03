import unittest
from mock import MagicMock, Mock
import json
import shutil
import sys
import os
from osapps.ad_connection import AdConnection

class TestAdConnectionTestCase(unittest.TestCase):
    TMP_DIRECTORY = "/tmp/feedback"
    
    def setUp(self):
        try:
            shutil.rmtree(self.TMP_DIRECTORY)
        except:
            pass #Could not erase feedback folder
                   
        self.test_object = AdConnection()

    def test_default_endpoint_is_localhost(self):
        self.test_object = AdConnection('invalid_path')
        self.assertEqual("http://localhost:3000", self.test_object._endpoint_server)
                         
    def test_set_endpoint_is_respected(self):
        filename = self.TMP_DIRECTORY + "/endpoint.json"
        os.makedirs(self.TMP_DIRECTORY)
        expected_endpoint='http://testendpoint:9999'
        with open(filename, 'w+') as f:
            f.write(json.dumps({'endpoint': expected_endpoint})) 

        self.test_object = AdConnection(filename)
        
        self.assertEqual(expected_endpoint, self.test_object._endpoint_server)
