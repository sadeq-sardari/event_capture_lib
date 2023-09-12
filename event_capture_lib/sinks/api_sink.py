import json
import warnings
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from event_capture_lib.sinks.base_sink import BaseEventSink

warnings.filterwarnings("ignore")


class ApiEventSink(BaseEventSink):
    def __init__(self, limit, api_url: str, auth_key: str):
        self._api_url = api_url
        self._auth_key = auth_key
        super().__init__(limit)

    @staticmethod
    def default_serializer(data):
        if isinstance(data, datetime):
            return data.strftime('%Y-%m-%d %H:%M:%S.%f')
        else:
            return str(data)

    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_fixed(2))
    def _sender(self, events):
        data = {'logs': events}
        data = json.dumps(data, default=self.default_serializer)

        rsp = requests.post(self._api_url, data=data, headers={'auth-key': self._auth_key,
                                                               'content-type': 'application/json'})
        if not rsp.status_code == 200:
            raise Exception('status code was not 200')
