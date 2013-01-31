from browser_button_presenter import BrowserButtonPresenter
from browser_button_view import BrowserButtonView
from browser_button_model import BrowserButtonModel
from osapps.app_launcher import AppLauncher

class BrowserButton():
   def __init__(self):
      self._button = BrowserButtonView()
      BrowserButtonPresenter(self._button, BrowserButtonModel(), AppLauncher())

   def get_button(self):
      return self._button

