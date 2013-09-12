'''
This is the main SaltEventsDaemon class. It holds all the logic that listens 
for events, collects events and starts all the workers to dump data.
'''

import threading
import logging
import copy

log = logging.getLogger(__name__)

class SaltEventsdWorker(threading.Thread):
    '''
    The worker for the salt-eventsd that pumps the data to the desired backend
    '''

    def __init__(self,
                 qdata,
                 name,
                 event_map,
                 backends):

        threading.Thread.__init__(self)
        self.setName(name)

        self.events = qdata
        self.event_map = event_map
        self.backends = backends

        self.active_backends = {}

    def run(self):
        '''
        start method of the worker that runs
        in its own thread
        '''
        log.info("{0} started".format(threading.currentThread().getName()))
        self._store_data()

    def _init_backend(self, backend):
        '''
        creates a new backend-worker
        '''
        setup_backend = copy.deepcopy( self.backends[backend] )
        setup_backend.setup()
        self.active_backends[backend] = setup_backend

    def _cleanup(self):
        '''
        makes sure that all the workers that were started are
        cleaning up their data and close their connections (if any)
        '''
        for (name, backend) in self.active_backends.items():
            backend.shutdown()

    def _store_data(self):
        '''
        loops through all the events and matches events against the desired
        backends from the config. if it matches, the the backend gets initiated
        and the event is passed to the backend with the backend-settings. the 
        backend takes care of pushing the data further.
        '''

        # look through all the events and pass them on to the corresponding 
	# backend each available backend is started only, if an event requires
	# it.
        for entry in self.events:
            for event in self.event_map.keys():

                event_set = None

                # check if the event matches any of our tags from the config
                if( self.event_map[event]['tag'].match( entry['tag'] ) ):

                    # if we have match, use that settings for this event
                    event_set = self.event_map[event]

                    # if the event has a subs-section, check the sub-events if 
		    # they match. if so, use these settings for this event. 
                    if( self.event_map[event].has_key('subs') ):

                        for subevent in self.event_map[event]['subs'].keys():

                            # check for 'fun'- or 'tag'-field as these are the 
			    # fields we filter by. we check for both and put 
			    # the event into the corresponding backend which 
			    # we might have to create prior to adding an event
                            if( self.event_map[event]['subs'][subevent].has_key('fun') ):
                                if( self.event_map[event]['subs'][subevent]['fun'].match( entry['data']['fun'] ) ):
                                    event_set = self.event_map[event]['subs'][subevent]

                            elif( self.event_map[event]['subs'][subevent].has_key('tag') ):
                                if( self.event_map[event]['subs'][subevent]['tag'].match( entry['data']['fun'] ) ):
                                    event_set = self.event_map[event]['subs'][subevent]

                    if not event_set:
                        log.error("event '{0}' not found in config".format(entry))

                    else:
                        # if the matched event_set still has (not matching) 
			# 'subs', remove them
                        if( event_set.has_key('subs') ):
                            del event_set['subs']

                        log.debug("")
                        log.debug("event match details:")
                        log.debug("event_set: {0}".format(event_set))
                        log.debug("event: {0}".format(entry))
                        log.debug("")

                        # if the backend for this type of event has not 
                        # been initiated yet, take care of that
                        if not ( event_set['backend'] in self.active_backends.keys() ):
                            self._init_backend(event_set['backend'])

                        # finally send that event to the backend including
			# the config-set for this event
                        self.active_backends[ event_set['backend'] ].send(entry, event_set)

        # have all backends clean up their cleanup
        self._cleanup()

