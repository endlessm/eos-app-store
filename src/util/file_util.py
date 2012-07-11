import os

DATA_DIRECTORY = os.path.expanduser("~/.endlessm")

def default_config_dir_name():
    if not os.path.exists(DATA_DIRECTORY):
        os.mkdir(DATA_DIRECTORY)
    return DATA_DIRECTORY

def get_file_path_in_config_dir(filename, dirname=default_config_dir_name()):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    return dirname + "/" + filename
