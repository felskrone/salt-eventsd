'''
this Worker takes care of return-data being returned by a minion.
it takes care of dumping the 'return'-field into the database
after its json-encoded and base64 converted.
'''

# import and setup logger first, so we can catch
# missing libraries on imports
import logging
import requests
import json

log = logging.getLogger(__name__)


class Bench_Worker(object):
    '''
    takes care of dumping 'return'-data into the database
    '''
    # the settings for the mysql-server to use
    creds = {}

    name = "Bench_Worker"
    thread_id = None

    def setup(self, thread_id, **kwargs):
        '''
        init the connection and do other necessary stuff
        '''
        self.thread_id = thread_id

        # keep track of the events dumped
        self.dumped = 0

        log.info("{0}# Worker '{1}' initiated".format(
            self.thread_id,
            self.name,
        ))

    def shutdown(self):
        '''
        close the connection to the mysql-server and maybe
        do some other cleanup if necessary
        '''
        log.debug("Worker '{0}' shut down".format(self.name))

    def send(self, entry, event_set):
        '''
        this has to be present in any Worker for the salt-eventsd.
        It receives events with their corresponding setting and
        passes it on to a handler-function
        '''
        # print("")

        # print(entry)
        # print("")
        # print(event_set)

        # print("")

        pass
