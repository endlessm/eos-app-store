class DesktopLayout(object):
    
    ICON_WIDTH = 64
    ICON_HEIGHT = 64
    DND_ICON_WIDTH = 48
    LABEL_WIDTH_IN_PIXELS = 112
    HORIZONTAL_SPACING = 64
    VERTICAL_SPACING = 64
    MAX_ICONS_IN_ROW = 7
    MAX_ROWS_OF_ICONS = 4
    
    @classmethod
    def get_spacer_width(cls):
        return (DesktopLayout.LABEL_WIDTH_IN_PIXELS - DesktopLayout.ICON_WIDTH) / 2
    
    @classmethod
    def get_separator_width(cls):
        return DesktopLayout.ICON_WIDTH + DesktopLayout.HORIZONTAL_SPACING - DesktopLayout.LABEL_WIDTH_IN_PIXELS