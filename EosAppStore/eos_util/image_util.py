import os
from gi.repository.GdkPixbuf import Pixbuf
from EosAppStore.eos_util import path_util
from EosAppStore.eos_log import log

def load_pixbuf(image_name):
    try:
        return Pixbuf.new_from_file(image_path(image_name))
    except Exception as e:
        log.error("An error occurred trying to load image. Loading default", e)
        return Pixbuf.new_from_file(image_path('generic-app.png'))

def image_path(image_name):
    path = os.path.abspath(os.path.join(path_util.SHARED_IMAGES_DIRECTORY, image_name))
    return path

def scrub_image_path(path):
    if not path or not os.path.exists(path):
        return None

    return path
