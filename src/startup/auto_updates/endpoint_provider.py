import os
from urlparse import urlparse

_DEFAULT_ENDLESS_URL = "http://apt.endlessdevelopment.com/updates"
_endless_home_path = os.path.expanduser("~/.endlessm")
_endless_mirror_file = os.path.join(_endless_home_path, "mirror")

def get_endless_url():
    _endless_url_setup()

    if os.path.exists(_endless_mirror_file):
        with open(_endless_mirror_file, "r") as f:
            url = f.read()
    else:
        url = _DEFAULT_ENDLESS_URL
        with open(_endless_mirror_file, "w") as f:
            f.write(_DEFAULT_ENDLESS_URL)

    return url

def set_endless_url(url):
    _endless_url_setup()

    with open(_endless_mirror_file, "w") as f:
        f.write(url)

def _endless_url_setup():
    if not os.path.exists(_endless_home_path):
        os.makedirs(_endless_home_path)

def reset_url():
    set_endless_url(_DEFAULT_ENDLESS_URL)
