import unittest
from mock import Mock, call

from eos_widgets.abstract_notifier import AbstractNotifier

class AbstractNotifierTest(unittest.TestCase):
    def setUp(self):
        self._test_object = Sample()

        self._mock_master = Mock()
        self._listener1 = self._mock_master.listener1
        self._listener2 = self._mock_master.listener2
        self._listener3 = self._mock_master.listener3

        self._test_object.add_listener(Sample.EVENT1, self._listener1)
        self._test_object.add_listener(Sample.EVENT2, self._listener2)
        self._test_object.add_listener(Sample.EVENT3, self._listener3)

    def test_listeners_get_notified(self):
        self._test_object.notify_event1()
        self._test_object.notify_event3()
        self._test_object.notify_event2()
        self._test_object.notify_event1()

        expected_calls = [ call.listener1(), 
                        call.listener3(), 
                        call.listener2(), 
                        call.listener1(), 
                        ]
        self.assertEquals(self._mock_master.mock_calls, expected_calls)

    def test_dont_blow_up_if_trying_to_notify_an_event_that_no_one_is_listening_for(self):
        self._test_object.notify_event4()

class Sample(AbstractNotifier):
    EVENT1 = "event1"
    EVENT2 = "event2"
    EVENT3 = "event3"
    EVENT4 = "event4"

    def notify_event1(self):
        self._notify(self.EVENT1)
        
    def notify_event2(self):
        self._notify(self.EVENT2)

    def notify_event3(self):
        self._notify(self.EVENT3)

    def notify_event4(self):
        self._notify(self.EVENT4)
