class DesktopLayout(object):
    
    ICON_WIDTH = 64
    ICON_HEIGHT = 64
    DND_ICON_WIDTH = 48
    LABEL_WIDTH_IN_PIXELS = 112
    HORIZONTAL_SPACING = 64
    VERTICAL_SPACING = 64
    MAX_ICONS_IN_ROW = 7
    MAX_ROWS_OF_ICONS = 4
    TOP_PADDING_BUFFER = 50

    @classmethod
    def calculate_total_top_padding(cls, *widgets):
        total = 0
        for widget in widgets:
            total += widget.get_allocation().height
        return total - cls.TOP_PADDING_BUFFER

    @classmethod
    def calculate_max_columns(cls):
        return cls.MAX_ICONS_IN_ROW

    @classmethod
    def number_of_icons(cls):
        return (cls.MAX_ICONS_IN_ROW * cls.MAX_ROWS_OF_ICONS) - 1
    
    @classmethod
    def get_spacer_width(cls):
        return (cls.LABEL_WIDTH_IN_PIXELS - cls.ICON_WIDTH) / 2
    
    @classmethod
    def get_separator_width(cls):
        return cls.ICON_WIDTH + cls.HORIZONTAL_SPACING - cls.LABEL_WIDTH_IN_PIXELS
