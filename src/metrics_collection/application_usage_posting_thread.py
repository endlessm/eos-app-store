from threading import Thread
class ApplicationUsagePostingThread(Thread):
    SLEEP_TIME = 60

    def __init__(self, application_usage_posting_util):
        super(ApplicationUsagePostingThread, self).__init__()
        self.setDaemon(True)

        self._application_usage_posting_util = application_usage_posting_util

    def run(self):
        while True:
            time.sleep(self.SLEEP_TIME)

            self._application_usage_posting_util.collect_and_send_data()

