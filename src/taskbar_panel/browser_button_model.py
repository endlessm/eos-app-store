from eos_util.locale_util import LocaleUtil

class BrowserButtonModel():
   def __init__(self, locale_util=LocaleUtil()):
      self._locale_util = locale_util

   def get_exploration_center_url(self):
      return "file:/usr/share/endlessm/exploration_center/index.html?lang={0}#newspaper".format(self._locale_util.get_locale())
