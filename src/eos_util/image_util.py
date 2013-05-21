import os
from gi.repository.GdkPixbuf import Pixbuf

from eos_log import log

SHARED_DATA_DIRECTORY = os.environ["XDG_DATA_DIRS"].split(":")[0] if os.environ["XDG_DATA_DIRS"] else "/usr/share"

SHARED_IMAGES_DIRECTORY = os.path.join (SHARED_DATA_DIRECTORY,"EndlessOS/images")

def load_pixbuf(image_name):
    try:
        return Pixbuf.new_from_file(image_path(image_name))
    except Exception as e:
        log.error("An error occurred trying to load image. Loading default", e)
        return Pixbuf.new_from_file(image_path('endless.png'))

def image_path(image_name):
    path = os.path.abspath(os.path.join(SHARED_IMAGES_DIRECTORY, image_name))
    return path

def scrub_image_path(path):
    if not path or not os.path.exists(path):
        return None

    return path
