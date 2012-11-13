import gtk

def get_width():
    screen = gtk.gdk.Screen() #@UndefinedVariable
    num_of_monitors = screen.get_n_monitors()
    return screen.get_width() / num_of_monitors

def get_height():
    screen = gtk.gdk.Screen() #@UndefinedVariable
    return screen.get_height()
    
class ScreenUtil:
    
    WORKING_AREA_OFFSET = 0
    
    @classmethod
    def get_offset(cls):
        return cls.WORKING_AREA_OFFSET
    
    @classmethod
    def set_offset(cls, value):
        cls.WORKING_AREA_OFFSET = value