from metrics.async_task_launcher import AsyncTaskLauncher
from metrics.metrics_send_process import MetricsSendProcess
from metrics.metrics_connection import MetricsConnection

class FeedbackManager():
    
    def __init__(self, metrics_worker_pool=AsyncTaskLauncher(MetricsSendProcess)):
        self._pool = metrics_worker_pool
        self._url_context = "feedbacks"
        self._file_name = "feedback.json"
        self._form_param_name = "feedback"
    

    def _create_connection(self):
        return MetricsConnection(self._url_context, self._form_param_name)

    def write_data(self, data):
        self._pool.launch_async([data, self._file_name, self._create_connection()])
