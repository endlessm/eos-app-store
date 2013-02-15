import sys
import shutil
import json
import unittest
import os
from mock import Mock, call

from metrics_collection.application_usage_sender import ApplicationUsageSender

class TestApplicationUsageSender(unittest.TestCase):
    TMP_DIRECTORY = "/tmp/app_sender"
    EXPECTED_FILE = os.path.join(TMP_DIRECTORY, "application_usage.json")

    def setUp(self):
        try:
            shutil.rmtree(self.TMP_DIRECTORY)
        except:
            pass #Could not erase feedback folder

        self._mock_metrics_connection = Mock()
        self._test_object = ApplicationUsageSender(self._mock_metrics_connection, self.TMP_DIRECTORY)

    def test_send_data_passes_data_to_metrics_connection(self):
        mock_data = self._create_json(u'newMessage', u'newTime', u'newBug')
        self._test_object.send_data(mock_data)
        self._mock_metrics_connection.send.assert_called_once_with(mock_data)

    def test_send_data_appends_cached_data(self):
        self._mock_metrics_connection.send = Mock(return_value = False)
        test_data1 = self._create_json(u'message', u'time', u'bug')
        self._test_object.send_data(test_data1)

        test_data2 = self._create_json(u'newMessage', u'newTime', u'newBug')
        self._mock_metrics_connection.send = Mock(return_value = True)
        self._test_object.send_data(test_data2)
        expected_data = [test_data1,test_data2]

        self.assertEquals(self._get_usage_from_file(), [])
        self._mock_metrics_connection.send.assert_calls([call([test_data1]), call(test_data2)])

    def _get_usage_from_file(self):
        usage_file = open(self.EXPECTED_FILE)
        loaded_usage = json.load(usage_file)
        usage_file.close()
        return loaded_usage

    def _create_json(self, message, timestamp, is_bug):
        return {u'message': message, u'timestamp': timestamp, u'bug': is_bug}
