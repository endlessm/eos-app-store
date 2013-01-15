from ldtp import *
from ldtp_helper import LdtpHelper

class AppStoreManipulator():
   def __init__(self):
      self._ldtp_helper = LdtpHelper()

   def click_through(self):
      self._ldtp_helper.click_on("add_remove_apps")
      self._ldtp_helper.click_on("folder_tab")
      self._ldtp_helper.click_on("close_app_store")


