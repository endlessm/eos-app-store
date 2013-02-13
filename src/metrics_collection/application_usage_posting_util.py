from application_usage_sender import ApplicationUsageSender

class ApplicationUsagePostingUtil():
    def __init__(self, app_tracker, application_usage_sender=ApplicationUsageSender()):
        self._app_tracker = app_tracker

    def collect_and_send_data(self):
        # Get collected data
        #self._time_in_application_tracker.get_usage_data()

        # Convert data to json
        # ???

        # Send collected data
        # self._metric_send_process.do_stuff(??)

        # Clear captured data
        #self._time_in_application_tracker.get_usage_data()
        pass
