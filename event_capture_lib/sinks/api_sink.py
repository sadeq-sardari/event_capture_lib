import pickle
import warnings

import requests
import json
from tenacity import retry, stop_after_attempt, wait_fixed

from base_sink import BaseEventSink

warnings.filterwarnings("ignore")


class ApiEventSink(BaseEventSink):
    def __init__(self, limit, api_url: str, auth_key: str):
        self._api_url = api_url
        self._auth_key = auth_key
        super().__init__(limit)

    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_fixed(2))
    def _sender(self, events):
        data = json.dumps(self.__prepare_events(events))
        requests.post(self._api_url, json=data, headers={'auth_key': self._auth_key})

    @staticmethod
    def __prepare_events(events):
        for i in events:
            f = pickle.loads(pickle.dumps(i, pickle.HIGHEST_PROTOCOL))  # fast deep copy
            try:
                f['timestamp'] = f['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')
            except (AttributeError, TypeError):
                pass
            yield f
