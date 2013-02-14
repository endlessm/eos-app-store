import os
from metrics.abstract_send_process import AbstractSendProcess
from metrics.metrics_connection import MetricsConnection

class ApplicationUsageSender(AbstractSendProcess):
    FILENAME = 'application_usage.json'
    def __init__(self, metrics_connection = MetricsConnection(form_param_name="time_in_activities"), directory_name=AbstractSendProcess.DEFAULT_DIRNAME):
        super(ApplicationUsageSender, self).__init__(self.FILENAME, metrics_connection, directory_name)
        self._metrics_connection = metrics_connection

    def send_data(self, data):
        self._save_data_item(data)

        data_list = [data_item for data_item in self._get_data_from_file() if self._metrics_connection.send(data_item) == False]

        self._save_data_to_file(data_list)
