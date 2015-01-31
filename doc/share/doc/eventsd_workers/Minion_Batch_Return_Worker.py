'''
this Worker takes care of return-data being returned by a minion.
it takes care of dumping the 'return'-field into the database
after its json-encoded and base64 converted.
'''

# import and setup logger first, so we can catch
# missing libraries on imports
import logging
import redis

log = logging.getLogger(__name__)


class Minion_Batch_Return_Worker(object):
    '''
    takes care of dumping 'return'-data into the database
    '''
    # the settings for the mysql-server to use
    settings = {}
    name = "Minion_Batch_Return_Worker"
    thread_id = None

    def setup(self, thread_id, **kwargs):
        '''
        Setup the worker and read all settings
        '''
        self.thread_id = thread_id

        # get the settings from the main config in kwargs
        if 'worker_settings' in kwargs:
            if self.name in kwargs['worker_settings']:
                self.settings.update(kwargs['worker_settings'][self.name])
            elif 'all' in kwargs['worker_settings']:
                self.settings.update(kwargs['worker_settings']['all'])
            else:
                log.info('{0}# no settings loaded from config'.format(self.thread_id))

        self.redis_host = self.settings['redis-host']
        self.redis_port = self.settings['redis-port']

        # keep track of the events dumped
        self.dumped = 0

        log.info("{0}# Worker '{1}' initiated".format(self.thread_id, self.name))

    def shutdown(self):
        '''
        '''
        log.info("{0}# dumped {1} events to {2}".format(
            self.thread_id,
            self.dumped,
            self.redis_host,
        ))

    def send_batch(self, events):
        """
        Get all events
        """
        r = redis.StrictRedis(
            host=self.redis_host,
            port=self.redis_port,
        )

        pipe = r.pipeline()

        for event_tuple in events:
            event = event_tuple[0]
            # event_set = event_tuple[1]

            pipe.set("{0}".format(
                event["data"]["jid"]),
                event["data"]["return"],
            )

        pipe.execute()
