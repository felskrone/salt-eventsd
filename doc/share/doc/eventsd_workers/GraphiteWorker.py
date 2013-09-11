'''
This is the main SaltEventsDaemon class. It holds all the logic that listens 
for events, collects events and starts all the workers to dump data.
'''

import simplejson
import threading
from base64 import b64encode
import logging
import time

log = logging.getLogger(__name__)

class GraphiteWorker():


    def setup(self):
        log.info("setting up graphite backend")
#        self.sock = socket.socket()
#        self.sock.connect((self.hostname, self.carbon_port))

        self.hostname = "graphite.intern.webpack.hosteurope.de"
        self.carbon_port = 2003
        self.dumped = 0
        self.name = "GraphiteWorker"

    def shutdown(self):
        log.info("dumped {0} events to {1}".format(self.dumped,
                                                   self.hostname))

        log.info("closing socket to server {0}".format(self.hostname))
        log.debug("Worker '{0}' shut down".format(self.name))
#        self.sock.close()


    def send(self, 
             data, 
            event_set):

        log.info("received data {0}".format(data))
        log.info("received event_set {0}".format(event_set))
        self._store(data, event_set)


    def _store(self,
               event,
               event_set):

        # keep track of the queue_entries dumped
        dumped = 0 

        # dump all the data we have received depending on the type

        try:
            # create a shortcut to various data

            metric = event_set['metric']
            src_dict = event_set['dict_name']
            src_fld = event_set['fields'][0]
            src_data = event[src_dict]

            log.info("sending message: {0} {1} {2}".format(metric, 
                                                           src_data[ str(src_fld) ],
                                                           int(time.time())))
                
            self.dumped += 1

        except Exception as excerr:
            log.critical("dont know how to handle:'{0}'".format(
                                                            event)
                                                         )   
            log.exception(excerr)

