import datetime

from eos_util.locale_util import LocaleUtil

class TimeDisplayPluginModel():
    def __init__(self, locale_util=LocaleUtil()):
        self._locale_util = locale_util
    
    def get_date_text(self):
        return self._locale_util.format_date_time(datetime.datetime.now()).upper()
