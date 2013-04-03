import os
import gtk
from eos_log import log

try:
    SHARED_DATA_DIRECTORY = os.environ['ENDLESS_SHARED_DATA_DIR']
except:
    SHARED_DATA_DIRECTORY = os.path.abspath("/usr/share/endlessm")

SHARED_IMAGES_DIRECTORY = os.path.join(SHARED_DATA_DIRECTORY,"images")


def load_pixbuf(image_name):
    try:
        return gtk.gdk.pixbuf_new_from_file(image_path(image_name))
    except Exception as e:
        log.error("An error occurred trying to load image. Loading default", e)
        return gtk.gdk.pixbuf_new_from_file(image_path('endless.png'))

def image_path(image_name):
    path = os.path.abspath(os.path.join(SHARED_IMAGES_DIRECTORY, image_name))

    # Try to use our local ~/images directory if image load fails
    if not os.path.exists(path):
        path = os.path.abspath(os.path.join("..", "images", image_name))

    return path

def scrub_image_path(path):
    if not path or not os.path.exists(path):
        return None

    return path
