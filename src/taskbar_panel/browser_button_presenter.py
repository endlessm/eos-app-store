
from browser_button_constants import  BrowserButtonConstants

class BrowserButtonPresenter():
   def __init__(self, view, model, browser_launcher):
      view.add_listener(BrowserButtonConstants.CLICK_EVENT, lambda: browser_launcher.launch_browser())


