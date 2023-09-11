import time

from base import EventCaptureBuilder
from sinks import StdoutEventSink

event_capture = EventCaptureBuilder([],
                                    {"project": 'dummy'})

event_capture.add_sink(StdoutEventSink(1))

s = time.perf_counter()


def func1(ev1):
    ev1.e.func1 = "func1"


def func2(ev1):
    ev1.e.func2 = "func2"


with event_capture.context_manager("test_") as ev:
    func1(ev)
    ev.snapshot_start('start')
    func2(ev)
    ev.snapshot_end('start')

with event_capture.context_manager('timer_1') as ctx:
    # time.sleep(0)
    pass

with event_capture.context_manager('timer_2'):
    # time.sleep(0)
    ev = event_capture.new_event('normal')
    ev.save()


@event_capture.sync_timer('mufunc')
def myfunc():
    # time.sleep(0)
    # 1/ 0
    pass


myfunc()
e = time.perf_counter()
event_capture.flush()
print(e - s)
