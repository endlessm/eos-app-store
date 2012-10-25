import os
import gtk

try:
    SHARED_DATA_DIRECTORY = os.environ['ENDLESS_SHARED_DATA_DIR']
except:
#SHARED_DATA_DIRECTORY = os.path.abspath("/home/dev1/checkout/endless_os_desktop/usr/share/endlessm")
    SHARED_DATA_DIRECTORY = os.path.abspath("/usr/share/endlessm")
    
SHARED_IMAGES_DIRECTORY = os.path.join(SHARED_DATA_DIRECTORY,"images")


def load_pixbuf(image_name):
    image_path = os.path.join(SHARED_IMAGES_DIRECTORY, image_name)
    return gtk.gdk.pixbuf_new_from_file(image_path)

def image_path(image_name):
    return os.path.join(SHARED_IMAGES_DIRECTORY, image_name)

def scrub_image_path(image):
    if not image or image.endswith('.svg') or not os.path.exists(image):
        return image_path("endless.png")
    return image
