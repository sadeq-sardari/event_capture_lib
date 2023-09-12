import json

from event_capture_lib.sinks.base_sink import BaseEventSink


class StdoutEventSink(BaseEventSink):
    def __init__(self, limit):
        super().__init__(limit)

    def _sender(self, events):
        for i in events:
            f = json.dumps(i, ensure_ascii=False, default=str)
            print(f)
