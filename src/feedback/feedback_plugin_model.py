import sys
from eos_util import image_util
from osapps.app_shortcut import AppShortcut
from eos_log import log
from application_store.installed_applications_model import InstalledApplicationsModel

class FeedbackPluginModel(object):
    def __init__(self, feedback_manager, time_provider):
        self._feedback_manager = feedback_manager
        self._time_provider = time_provider

    def submit_feedback(self, message, bug):
        data = {"message":message, "timestamp":self._time_provider.get_current_time(), "bug":bug}
        self._feedback_manager.write_data(data)
