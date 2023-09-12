import pickle
import time
import traceback
import warnings
from datetime import datetime, timedelta
from threading import Thread

import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from tenacity import retry, stop_after_attempt, wait_fixed

from event_capture_lib.sinks.base_sink import BaseEventSink

warnings.filterwarnings("ignore")

class ElasticEventSink(BaseEventSink):
    def __init__(self, limit, host: str, index_prefix: str):
        super().__init__(limit)
        self.__client = Elasticsearch(hosts=[host])
        self.__index_prefix = index_prefix
        t = Thread(target=self.elastic_search_daily_index_generator)
        t.start()

    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_fixed(2))
    def _sender(self, events):
        # insert events to elasticsearch
        bulk(self.__client, self.__prepare_events(events))

    def __prepare_events(self, events):
        for i in events:
            f = pickle.loads(pickle.dumps(i, pickle.HIGHEST_PROTOCOL))  # fast deep copy
            try:
                f['timestamp'] = f['timestamp'] - timedelta(minutes=210)  # for timezone
                f['timestamp'] = f['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')
            except (AttributeError, TypeError):
                pass
            yield {"_index": self.get_index(), **f}

    def get_index(self):
        today = str(datetime.now().date())
        index_name = self.__index_prefix + '-' + today
        return index_name

    def _elastic_search_daily_index_generator(self):
        """
        this function creates daily
        """
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        index_name = self.__index_prefix + '-' + tomorrow
        fmt = "yyyy-MM-dd HH:mm:ss.SSSSSS"
        idx_body = {
            "mappings": {
                "dynamic_date_formats": [fmt]
            },
            "settings": {
                "index": {
                    "number_of_shards": 3,
                    "number_of_replicas": 1
                }
            }
        }
        try:
            self.__client.indices.create(index=index_name,
                                         mappings=idx_body["mappings"],
                                         settings=idx_body["settings"])
        except elasticsearch.exceptions.RequestError as exception:
            if exception.args[1] == 'resource_already_exists_exception':
                pass
            else:
                traceback.print_exc()

        try:
            self.__client.indices.create(index=self.get_index(),
                                         mappings=idx_body["mappings"],
                                         settings=idx_body["settings"])
        except elasticsearch.exceptions.RequestError as exception:
            if exception.args[1] == 'resource_already_exists_exception':
                pass
            else:
                traceback.print_exc()
        print('done')

    def elastic_search_daily_index_generator(self):
        while True:
            try:
                self._elastic_search_daily_index_generator()
                time.sleep(60 * 60 * 12)
            except KeyboardInterrupt:
                return

