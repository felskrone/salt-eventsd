'''
this Worker can be used to insert data into Elasticsearch.
'''

# import and setup logger first, so we can catch
# missing libraries on imports
import logging

log = logging.getLogger(__name__)

try:
    import logging
    from socket import gethostname
    from elasticsearch import Elasticsearch
except ImportError as mis_lib:
    log.error('Failed to start worker: {0}'.format(mis_lib))
    log.exception(mis_lib)


class Elasticsearch_Worker(object):
    '''
    Inserts events into an Elasticsearch backend
    '''

    # the settings for connecting to Elasticsearch. Needs 'elasticsearch_host'
    # and 'elasticsearch_port' keys
    creds = {}

    name = "Elasticsearch_Worker"
    thread_id = None

    def setup(self, thread_id, **kwargs):
        '''
        Initialize the ES client and setup stuff
        '''
        self.thread_id = thread_id

        # get the credentials from the main config in kwargs
        if 'worker_credentials' in kwargs:
            if self.name in kwargs['worker_credentials']:
                self.creds.update(kwargs['worker_credentials'][self.name])
            elif 'all' in kwargs['worker_credentials']:
                self.creds.update(kwargs['worker_credentials']['all'])
            else:
                log.info('{0}# no creds loaded'.format(self.thread_id))

        self.conn = Elasticsearch(
            self.creds['elasticsearch_host'],
            port=self.creds['elasticsearch_port'])

        # keep track of the events dumped
        self.dumped = 0

        log.info("{0}# Worker '{1}' setup".format(self.thread_id, self.name))

    def shutdown(self):
        '''
        Any necessary cleanup
        '''
        log.info("{0}# dumped {1} events".format(self.name, self.dumped))

    def send(self, entry, event_set):
        '''
        this has to be present in any Worker for the salt-eventsd.
        It receives events with their corresponding setting and
        passes it on to a handler-function
        '''
        self._store(entry, event_set)

    def _store(self, event, event_set):
        '''
        the actual worker-function which parses the event-configuration
        and indexes the data into Elasticsearch
        '''

        try:
            # see if we have been configured to ignore events of this type
            if (('fun' in event['data'])
                    and (event['data']['fun'] in event_set['ignore'])):

                log.info("Ignoring event: {0}".format(event['data']['fun']))
                return

            # index the event
            result = self.conn.index(
                index=event_set['index'],
                doc_type=event_set['type'],
                body=event)

            self.dumped += 1
        except Exception as excerr:
            log.critical("{0}# dont know how to handle:'{1}'".format(
                self.thread_id,
                event))

            log.exception(excerr)
