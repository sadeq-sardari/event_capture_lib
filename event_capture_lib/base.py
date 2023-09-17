import traceback
from datetime import datetime
from functools import wraps
from time import perf_counter

from dotmap import DotMap
from sentry_sdk import capture_exception, push_scope


# noinspection PyShadowingNames
class EventCaptureBuilder:
    def __init__(self, sinks, base_meta: dict, enable_sentry=True):
        self.__sentry = enable_sentry
        self.__base_meta = base_meta
        self.__sinks = sinks
        self.context_manager = self.__build_ctx_manager()
        self.sync_timer = self.__build_sync_decorator()
        self.async_timer = self.__build_async_decorator()

    def __add_event_to_sinks(self, event):
        for i in self.__sinks:
            i.add_event(event)

    def __build_ctx_manager(self):
        add_event = self.__add_event_to_sinks
        get_event = self.new_event
        sentry = self.__sentry

        class EventContextManager:
            def __init__(self, event_name: str):
                self.__event = get_event(event_name)
                self.__event.e.timestamp = datetime.now()

            def __enter__(self):
                self.__time = perf_counter()
                return self.__event

            def __exit__(self, exc_type, exc_value, exc_traceback):
                if exc_traceback:
                    if sentry:
                        with push_scope() as scope:
                            scope.set_tag("logger", "event_capture")
                            capture_exception(exc_value)
                    exc = traceback.format_exc()
                    self.__event.e.exception = exc
                duration = round((perf_counter() - self.__time) * 1000, 2)  # in milliseconds
                self.__event.e.duration = duration
                add_event(self.__event.e.toDict())

        return EventContextManager

    def __build_async_decorator(self):
        def decorator(event_name=None):
            def middle(func, event_name=event_name):
                if not event_name:
                    event_name = func.__name__

                @wraps(func)
                async def inner(*args, **kwargs):
                    with self.context_manager(event_name=event_name):
                        result = await func(*args, **kwargs)
                    return result

                inner: func
                return inner

            return middle

        return decorator

    def __build_sync_decorator(self):
        def decorator(event_name=None):
            def middle(func, event_name=event_name):
                if not event_name:
                    event_name = func.__name__

                @wraps(func)
                def inner(*args, **kwargs):
                    with self.context_manager(event_name=event_name):
                        result = func(*args, **kwargs)
                    return result

                inner: func
                return inner

            return middle

        return decorator

    def __get_event_class(self):
        base_meta = DotMap(self.__base_meta.copy())
        add_event = self.__add_event_to_sinks

        class Event(object):
            def __init__(self, event_name):
                self.e = DotMap()
                self.time = perf_counter()
                self.e.meta = base_meta.copy()
                self.e.event_name = event_name
                self.e.timestamp = datetime.now()
                self._snapshots = {}
                self._final_snapshots = {}
                self.e.snapshots = self._final_snapshots

            def save(self):
                self.e.duration = round((perf_counter() - self.time) * 1000, 2)
                add_event(self.e.toDict())

            def snapshot_start(self, name: str):
                self._snapshots[name] = dict()
                self._snapshots[name]['start'] = datetime.now()
                self._snapshots[name]['name'] = name

            def snapshot_end(self, name: str):
                if name not in self._snapshots:
                    return
                self._snapshots[name]['duration'] = (round((datetime.now() -
                                                            self._snapshots[name]['start'])
                                                           .total_seconds() * 1000, 2))
                self._final_snapshots[name] = self._snapshots.pop(name)

        return Event

    def new_event(self, event_name):
        return self.__get_event_class()(event_name)

    def flush(self):
        for i in self.__sinks:
            i.flush()

    def add_sink(self, sink):
        self.__sinks.append(sink)
