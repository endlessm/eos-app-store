from notification_plugin import NotificationPlugin
from battery_view import BatteryView
from battery_model import BatteryModel
from battery_presenter import BatteryPresenter

class BatteryPlugin(NotificationPlugin):
    def __init__(self, icon_size):
        super(BatteryPlugin, self).__init__(icon_size)
        self._presenter = BatteryPresenter(BatteryView(self, icon_size), BatteryModel())

    def post_init(self):
        self._presenter.post_init()
    
    def execute(self):
        self._presenter.display_menu() 

        
           
