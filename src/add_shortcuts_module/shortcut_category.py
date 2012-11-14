class ShortcutCategory():
    def __init__(self, name='', active=False):
        self.category = name
        self.subcategories = []
        self.active = active