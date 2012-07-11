import gtk

def get_width():
    screen = gtk.gdk.Screen() #@UndefinedVariable
    num_of_monitors = screen.get_n_monitors()
        
    return screen.get_width() / num_of_monitors

def get_height():
    screen = gtk.gdk.Screen() #@UndefinedVariable
    return screen.get_height()