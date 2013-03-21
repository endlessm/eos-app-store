
from browser_button_constants import  BrowserButtonConstants

class BrowserButtonPresenter():
   def __init__(self, view, model, app_launcher):
      view.add_listener(BrowserButtonConstants.CLICK_EVENT, lambda: app_launcher.launch_browser())


