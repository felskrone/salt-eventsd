'''
This is the main SaltEventsDaemon class. It holds all the logic that listens
for events, collects events and starts all the workers to dump data.
'''

import time
import os
import simplejson
import sys
from re import compile
import salt.utils.event
import logging
import salt.log
from salteventsd.timer import ResetTimer
from salteventsd.loader import SaltEventsdLoader
from salteventsd.worker import SaltEventsdWorker
from salteventsd.backends import BackendMngr
import salteventsd.daemon
import signal
import zmq

log = logging.getLogger(__name__)


class SaltEventsDaemon(salteventsd.daemon.Daemon):
    '''
    The main daemon class where all the parsing, collecting
    and dumping takes place
    '''

    def __init__(self, config):
        self.opts = SaltEventsdLoader(config=config).getopts()
        self._pre_startup(self.opts)

        if type(self.opts) is not dict:
            log.info("Received invalid configdata, startup cancelled")
            sys.exit(1)

        self.config = self.opts['general']
        super(SaltEventsDaemon, self).__init__(self.config['pidfile'])

        # the map of events are stored here, loaded in _init_events()
        self.event_map = None
        self._init_events(self.opts['events'])

        self.backends = self._init_backends(self.config['backends'])
        log.info(self.backends)

        # the socket to listen on for the events
        self.sock_dir = self.config['sock_dir']

        # two possible values for 'node': master and minion
        # they do the same thing, just on different sockets
        self.node = self.config['node']

        # the id, usually 'master'
        self.nodeid = self.config['id']

        # the statefile where we write the daemon status
        self.state_file = self.config['state_file']

        # how many events to handle before updating the status
        self.state_timer = self.config['state_timer']

        # we dont know our pid (yet), its updated in run()
        self.pid = None

        # how many parallel workers to start max
        self.max_workers = self.config['max_workers']

        # the number of events to collect before starting a worker
        self.event_limit = self.config['event_limit']

        # a list to keep track of the currently running workers
        # this is mainly for debugging to check wether all started
        # workers are correctly joined over time so we dont leak memory
        self.running_workers = []

        # setup some counters used for the status
        self.events_han = 0
        self.events_rec = 0
        self.threads_cre = 0
        self.threads_join = 0

        # the timer thats write data to the database every x seconds
        # this is used to push data into the database even if
        # self.event_limit is not reached regularly
        self.ev_timer_ev = False
        self.ev_timer_intrvl = self.config['dump_timer']
        self.ev_timer = ResetTimer(
            self.ev_timer_intrvl,
            self,
        )

    def timer_event(self):
        '''
        This is called whenever the timer started in __init__()
        gets to the end of its counting loop
        '''
        self.ev_timer_ev = True

    def stop(self, signal, frame):
        '''
        We override stop() to brake our main loop
        and have a pretty log message
        '''
        log.info("Received signal {0}".format(signal))

        # if we have running workers, run through all and join() the ones
        # that have finished. if we still have running workers after that,
        # wait 5 secs for the rest and then exit. Maybe we should improv
        # this a litte bit more
        if len(self.running_workers) > 0:
            clean_workers = []

            for count in range(0, 2):
                for worker in self.running_workers:
                    if worker.isAlive():
                        clean_workers.append(worker)
                    else:
                        worker.join()
                        log.debug("Joined worker #{0}".format(worker.getName()))

                if len(clean_workers) > 0:
                    log.info("Waiting 5secs for remaining workers..")
                    time.sleep(5)
                else:
                    break

        log.info("salt-eventsd has shut down")

        # leave the cleanup to the supers stop
        try:
            super(SaltEventsDaemon, self).stop(signal, frame)
        except (IOError, OSError):
            os._exit(0)

    def start(self):
        '''
        We override start() just for our log message
        '''
        log.info("Starting salt-eventsd daemon")
        # leave the startup to the supers daemon, thats where all
        # the daemonizing and double-forking takes place
        super(SaltEventsDaemon, self).start()

    def run(self):
        '''
        This method is automatically called by start() from
        our parent class
        '''
        log.info("Initializing event-listener")
        self.pid = self._get_pid()
        self._write_state()
        self.listen()

    def _pre_startup(self, opts):
        '''
        Does a startup-check if all needed parameters are
        found in the configfile. this is really important
        because we lose stdout in daemon mode and exceptions
        might not be seen by the user
        '''
        required_general = [
            'sock_dir',
            'node',
            'max_workers',
            'id',
            'event_limit',
            'pidfile',
            'state_file',
            'state_timer',
            'dump_timer',
        ]

        for field in required_general:
            if field not in opts['general']:
                log.critical("Missing parameter " +
                             "'{0}' in configfile".format(field))
                sys.exit(1)

    def listen(self):
        '''
        The main event loop where we receive the events and
        start the workers that dump our data into the database
        '''
        # log on to saltstacks event-bus
        event = salt.utils.event.SaltEvent(
            self.node,
            self.sock_dir,
        )

        # we store our events in a list, we dont really care about an order
        # or what kind of data is put in there. all that is configured with the
        # templates configured in the configfile
        event_queue = []

        # start our dump_timer
        self.ev_timer.start()

        # this is for logline chronology so the timer-message always comes
        # _before_ the actual startup-message of the listening loop below :-)
        time.sleep(1)

        log.info("Entering main event loop")
        log.info("Listening on: {0}".format(event.puburi))

        # read everything we can get our hands on
        while True:
            # the zmq-socket does not like ^C very much, make the error
            # a little more graceful. alright, alright, ignore the damn thing,
            # we're exiting anyways...
            try:
                ret = event.get_event(full=True)
            except zmq.ZMQError:
                pass
            except KeyboardInterrupt:
                log.info('Received CTRL+C, shutting down')
                self.stop(signal.SIGTERM, None)

            if ret is None:
                continue

            # if we have not received enough events in to reach event_limit
            # and the timer has fired, dump the events collected so far
            # to the workers
            if(self.ev_timer_ev):
                if (len(self.running_workers) < self.max_workers) and \
                   (len(event_queue) > 0):

                    self._init_worker(event_queue)

                    # reset our queue to prevent duplicate entries
                    del event_queue[:]

                    # we reset the timer.ev_timer_ev  at the end of the loop
                    # so we can update the stats that are logged

            # filter only the events we're interested in. all events have a tag
            # we can filter them by. we match with a precompiled regex
            if 'tag' in ret:
                # filter out events with an empty tag. those are special
                if ret['tag'] != '':
                    # run through our configured events and try to match the
                    # current events tag against the ones we're interested in
                    for key in self.event_map.keys():
                        if self.event_map[key]['tag'].match(ret['tag']):
                            log.debug("Matching on {0}:{1}".format(key, ret['tag']))

                            prio = self.event_map[key].get('prio', 0)

                            # push prio1-events directly into a worker
                            if prio > 0:
                                log.debug('Prio1 event found, pushing immediately!')
                                self.events_han += 1
                                self._init_worker([ret])
                            else:
                                event_queue.append(ret)
                                self.events_han += 1

            # once we reach the event_limit, start a worker that
            # writes that data in to the database
            if len(event_queue) >= self.event_limit:
                # only start a worker if not too many workers are running
                if len(self.running_workers) < self.max_workers:
                    self._init_worker(event_queue)
                    # reset the timer
                    self.ev_timer.reset()

                    # reset our queue to prevent duplicate entries
                    del event_queue[:]
                else:
                    # FIXME: we need to handle this situation somehow if
                    # too many workers are running. just flush the events?
                    # there really is no sane way except queueing more and more
                    # until some sort of limit is reached and we care more about
                    # our saltmaster than about the collected events!
                    log.critical("Too many workers running, loosing data!!!")

            # a list for the workers that are still running
            clean_workers = []

            # run through all the workers and join() the ones
            # that have finished dumping their data and keep
            # the running ones on our list
            for worker in self.running_workers:
                if worker.isAlive():
                    clean_workers.append(worker)
                else:
                    worker.join()
                    log.debug("Joined worker #{0}".format(worker.getName()))
                    self.threads_join += 1

            # get rid of the old reference  and set a new one
            # FIXME: is this really neccessary?
            del self.running_workers

            self.running_workers = clean_workers
            self.events_rec += 1

            # we update the stats every 'received div handled == 0'
            # or if we recevied a timer event from our ResetTimer
            if (self.events_rec % self.state_upd) == 0:
                self._write_state()
            elif(self.ev_timer_ev):
                self._write_state()
                self.ev_timer_ev = False

        log.info("Listen loop ended...")

    def _get_pid(self):
        '''
        Get our current pid from the pidfile and fall back
        to os.getpid() if pidfile not present (in foreground mode)
        '''
        pid = None

        try:
            pidf = file(self.pidfile, 'r')
            pid = int(pidf.read().strip())
            pidf.close()
        except IOError:
            pid = os.getpid()
        return pid

    def _write_state(self):
        '''
        Writes a current status to the defined status-file
        this includes the current pid, events received/handled
        and threads created/joined
        '''
        try:
            # write the info to the specified log
            statf = open(self.state_file, 'w')
            statf.writelines(
                simplejson.dumps({
                    'events_received': self.events_rec,
                    'events_handled': self.events_han,
                    'threads_created': self.threads_cre,
                    'threads_joined': self.threads_join,
                })
            )

            # if we have the same pid as the pidfile, we are the running daemon
            # and also print the current counters to the logfile with 'info'
            if os.getpid() == self.pid:
                log.info("Running with pid {0}".format(self.pid))
                log.info("Events (han/recv): {0}/{1}".format(
                    self.events_han,
                    self.events_rec,
                ))
                log.info("Threads (cre/joi):{0}/{1}".format(
                    self.threads_cre,
                    self.threads_join,
                ))

            statf.write("\n")
            statf.close()
            sys.stdout.flush()
        except IOError as ioerr:
            log.critical("Failed to write state to {0}".format(self.state_file))
            log.exception(ioerr)
        except OSError as oserr:
            log.critical("Failed to write state to {0}".format(self.state_file))
            log.exception(oserr)

    def _init_backends(self, backends):
        '''
        Loads the backends defined in the config
        '''
        backend_mngr = BackendMngr(
            ['/usr/share/pyshared/salteventsd/', self.config['backend_dir']]
        )
        return backend_mngr.load_plugins()

    def _init_events(self, events={}):
        '''
        Creates a dict of precompiled regexes for all defined events
        from config for maximum performance.
        '''
        self.event_map = events
        # we precompile all regexes
        log.info("Initialising events...")

        for key in events.keys():
            # we compile the regex configured in the config
            self.event_map[key]['tag'] = compile(events[key]['tag'])
            log.info("Added event '{0}'".format(key))

            # if subevents are configured, also update them with
            # regex-matching object
            if 'subs' in events[key]:
                for sub_ev in events[key]['subs'].keys():
                    try:
                        self.event_map[key]['subs'][sub_ev]['fun'] = compile(events[key]['subs'][sub_ev]['fun'])
                    except KeyError:
                        pass

                    try:
                        self.event_map[key]['subs'][sub_ev]['tag'] = compile(events[key]['subs'][sub_ev]['tag'])
                    except KeyError:
                        pass

                    log.info("Added sub-event '{0}->{1}'".format(key, sub_ev))

    def _init_worker(self, qdata):
        '''
        The method dumps the data into a worker thread which
        handles pushing the data into different backends.
        '''
        self.threads_cre += 1

        log.info("Starting worker #{0}".format(self.threads_cre))

        # make sure we pass a copy of the list
        worker = SaltEventsdWorker(
            list(qdata),
            self.threads_cre,
            self.event_map,
            self.backends,
            **self.opts
        )

        worker.start()
        self.running_workers.append(worker)
