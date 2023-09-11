from threading import Thread


class BaseEventSink:

    def __init__(self, limit):
        self._event_list = []
        self._limit = limit
        self._tmp = []

    def add_event(self, event):
        self._event_list.append(event)
        if len(self._event_list) >= self._limit:
            self.flush()

    def flush(self):
        tmp = self._event_list[:]
        self._event_list.clear()
        self._tmp.clear()
        thread = Thread(target=self._sender, args=[tmp])
        thread.start()

    def _sender(self, events):
        raise NotImplemented()
