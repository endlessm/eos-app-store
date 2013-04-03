import unittest
import os.path
import logging

from eos_log import log

class LogTest(unittest.TestCase):
    def setUp(self):
        open("/tmp/endless-desktop.log", "w").close()

        logging.getLogger("EndlessOS").setLevel(logging.DEBUG)

    def test_debug_messages_show_up_log_file(self):
        message = "this is some debug content"

        log.debug(message)

        self._assert_messages_in_log(message, "EndlessOS", "DEBUG")

    def test_info_messages_show_up_log_file(self):
        message = "this is some info content"

        log.info(message)

        self._assert_messages_in_log(message, "EndlessOS", "INFO")

    def test_warn_messages_show_up_log_file(self):
        message = "this is some warning content"

        log.warn(message)

        self._assert_messages_in_log(message, "EndlessOS", "WARN")

    def test_error_messages_show_up_log_file(self):
        message = "this is some error content"

        log.error(message)

        self._assert_messages_in_log(message, "EndlessOS", "ERROR")

    def test_fatal_messages_show_up_log_file(self):
        message = "this is some fatal content"

        log.fatal(message)

        self._assert_messages_in_log(message, "EndlessOS", "CRITICAL")

    def test_stack_traces_show_up_log_file(self):
        message = "stackstuff"

        log.print_stack(message)

        self._assert_messages_in_log(message, 
                "EndlessOS", 
                "INFO",
                "eos_log_tests/log_test.py",
                "test_stack_traces_show_up_log_file"
                )

    def _assert_messages_in_log(self, *args):
        with open("/tmp/endless-desktop.log", "r") as f:
            log_contents = f.read()

        for arg in args:
            self.assertTrue(arg in log_contents, "\"" + arg + "\" was not found in the log")
