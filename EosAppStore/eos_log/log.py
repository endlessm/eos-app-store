import os.path
import logging
from traceback import format_list,extract_stack
from logging import FileHandler
import sys

_ENDLESS_LOG_FILE = "/var/log/endlessm/endless-desktop.log"
if not os.path.exists("/var/log/endlessm"):
    _ENDLESS_LOG_FILE = "/tmp/endless-desktop.log"

if '_eos_logger' not in globals():
    _eos_logger = logging.getLogger('EndlessOS')
    _eos_logger.setLevel(logging.WARN)
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    _eos_file_handler = FileHandler(_ENDLESS_LOG_FILE)
    _eos_file_handler.setFormatter(formatter)
    _eos_logger.addHandler(_eos_file_handler)

    if  os.environ.get("ENDLESS_VERBOSITY"):
        _eos_stream_handler = logging.StreamHandler()
        _eos_stream_handler.setFormatter(formatter)
        _eos_logger.addHandler(_eos_stream_handler)


def debug(message):
    """
    Log debug messages to the user's EndlessOS log file.
    Debugging messages are for developer use.
    """
    _eos_logger.debug(message)

def info(message):
    """
    Log info messages to the user's EndlessOS log file
    Info messages are for noteworthy events that are not necessarily
    erroneous behaviors.
    """
    _eos_logger.info(message)
    
def warn(message):
    """
    Log warn messages to the user's EndlessOS log file
    Warning messages are for problematic situations that don't have  
    don't actually effect the system or the end user's experience.
    """
    _eos_logger.warn(message)

def error(message, exception=None):
    """
    Log error messages to the user's EndlessOS log file
    Error messages are for problematic situations that will effect 
    either other system components or effect the end user's experience.  
    """
    _eos_logger.error(message)
    if exception:
        _eos_logger.exception(exception)

def fatal(message, exception=None):
    """
    Log fatal messages to the user's EndlessOS log file
    Fatal messages are for severe issues that will cause the system to
    no longer function.  These messages should be logged prior to the system 
    exiting. 
    """
    _eos_logger.fatal(message)
    if exception:
        _eos_logger.exception(exception)

def print_stack(message):
    """
    Log the current stacktrace to the user's EndlessOS log file
    """
    stack_trace = "".join(format_list(extract_stack()))
    _eos_logger.info(message + " - dumping stack\n" + stack_trace)
