from EosAppStore.eos_widgets.image_eventbox import ImageEventBox

class FolderEventBox(ImageEventBox):

    def __init__(self, image, width):
        super(FolderEventBox, self).__init__([image])

        self._image = image

        # Stretch the image to fit the desired width, maintaining its height
        # Note: the current implementation modifies the provided image object
        # To do: consider making a copy of the image object to stretch
        self._image.stretch_horizontal(width)

    def _draw_image(self, image, _draw_method, x, y, w, h):
        image.draw(_draw_method)
