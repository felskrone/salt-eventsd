# coding=utf-8

# python std lib
import logging

log = logging.getLogger(__name__)


class Bench_Worker(object):
    '''
    takes care of dumping 'return'-data into the database
    '''
    name = "Bench_Worker"
    thread_id = None

    def setup(self, thread_id, **kwargs):
        '''
        init the connection and do other necessary stuff
        '''
        self.thread_id = thread_id

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
        log.debug(entry)
        log.debug(event_set)
