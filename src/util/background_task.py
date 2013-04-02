import gobject

def do_when_idle(fn):
    '''This will run the wrapped call when the main thread is idle care should be taken when using this as bad things can happen if chained incorrectly'''
    def wrapper(self, *args):
        gobject.idle_add(fn, self, *args)
    return wrapper