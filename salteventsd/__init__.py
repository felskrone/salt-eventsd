#!/usr/bin/python

import time
import os
import simplejson
import sys
from threading import Thread
from re import compile
from base64 import b64encode
import logging
import salt.utils.event
from salteventsd.configreader import Configreader
from salteventsd.logger import Logger
from salteventsd.timer import ResetTimer
from salteventsd.mysql import MysqlConn
import salteventsd.daemon
import signal
import zmq

class SaltEventsDaemon(salteventsd.daemon.Daemon):

    def __init__(self):

        self.opts = Configreader().load('/etc/salt/eventsd.conf')

        self.log = logging.getLogger('salt-eventsd')

        self.pre_startup(self.opts)

        if type(self.opts) is not dict:
            self.log.info("Received invalid configdata, startup cancelled")
            sys.exit(1)

        self.config = self.opts['general']
        super(SaltEventsDaemon, self).__init__(self.config['pidfile'])

        self.initMysql(**self.opts['mysql'])
        self.initEvents(self.opts['events'])

        # the socket to listen on for the events
        self.sock_dir = self.config['sock_dir']

        # two possible values for 'node': master and minion
        # they do the same thing, just on different sockets
        self.node = self.config['node']
        # the id
        self.id = self.config['id']

        # the statefile where we write the daemon status
        self.state_file = self.config['state_file']
        # how many events to handle before updating the status
        self.state_upd = self.config['state_upd']
        # we dont know our pid (yet)
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
        self.ev_timer = ResetTimer(self.ev_timer_intrvl, 
                                 self)

        # this is used to break the main while-loop
        self.shutdown = False


    def timerEvent(self):
        self.ev_timer_ev = True
        self.log.debug("event_timer fired")

    def stop(self,
             signal,
             frame):
        # leave the cleanup to the supers stop
        self.log.info("salt-eventsd has shut down")
        super(SaltEventsDaemon, self).stop(signal, frame)

    def start(self):
        self.log.info("starting salt-eventsd daemon")
        # leave the startup to the supers daemon 
        super(SaltEventsDaemon, self).start()

    def run(self):
        self.log.info("starting event listener")
        self.pid = self.getPid()
        self.writeState()
        self.listen()


    def pre_startup(self,
                    opts):
        # do a startup-check if all needed parameters are 
        # found in the configfile. this is really important
        # because we lose stdout in daemon mode
        required_general = [   'sock_dir',
                               'node',
                               'max_workers',
                               'id',
                               'event_limit',
                               'pidfile',
                               'state_file',
                               'state_upd',
                               'dump_timer'
                           ]

        for field in required_general:
            if field not in opts['general']:
                self.log.critical("Missing required parameter '{0}' in configfile".format(field))
                sys.exit(1)

        required_mysql = [  'username',
                            'password',
                            'db',
                            'host'
                         ]

        for field in required_mysql:
            if field not in opts['mysql']:
                self.log.critical("Missing required parameter '{0}' in section 'mysql'".format(field))
                sys.exit(1)


        # here we check if all configured events have the required fields       
        # because there are no optional ones!
        required_events = [ 'tag',
                            'mysql_tab',
                            'template',
                            'dict_name',
                            'fields'
                          ]
        for field in required_events:
            for tag in opts['events'].keys():
                if field not in opts['events'][tag]:
                    self.log.critical("Missing required parameter '{0}' in event '{1}'".format(field, tag))
                    sys.exit(1)


    def listen(self):
        event = salt.utils.event.SaltEvent(
                self.node,
                self.sock_dir,
                id = self.id
                )

        # we store our events in a list, we dont really care about an order
        # or what kind of data is put in there. all that is configured with the
        # sql-template configured in the configfile
        event_queue = []

        # start our dump_timer
        self.ev_timer.start()

        # this is for logline chronology so the time-message always comes _before_
        # the actual startup-message of the listening loop below :-)
        time.sleep(1)

        # read everything we can get our hands on
        self.log.info("entering main event loop")

        self.log.info("listening on: {0}".format(event.puburi))


        while True:
            if self.shutdown:
                break
            try:
                ret = event.get_event(full=True)
            except zmq.ZMQError as e:
                pass
            if ret is None:
               continue

            # if the timer has expired, we may have not received enough
            # events in the queue to reach event_limit, in that case we dump
            # the data anyway to have it in the database
            if(self.ev_timer_ev):
                if (len(self.running_workers) < self.max_workers) and \
                   (len(event_queue) > 0):

                    self.log.info("timer fired, starting worker #{0}".format( self.threads_cre+1 ))
                    worker = Thread(target=self.sendToMysql(event_queue), 
                                    name=str(self.threads_cre+1))
                    self.running_workers.append(worker)
                    worker.start()
                    self.threads_cre += 1

                    # reset our queue to prevent duplicate entries
                    del event_queue[:]

                    # we reset the timer.ev_timer_ev  at the end of the loop 
                    # so we can update the stats that are logged


            # filter only the events we're interested in
            if( 'tag' in ret ):
                if( ret['tag'] != '' ):
                    for key in self.event_struct.keys():
                        if( self.event_struct[key]['tag'].match( ret['tag'] ) ):
                            self.log.debug("matching on {0}:{1}".format(key, ret['tag']))
                            event_queue.append(ret)
                            self.events_han += 1

            # once we reach the event_limit, start a worker that
            # writes that data in to the database
            if len(event_queue) >= self.event_limit:

                # only start a worker if not too many workers are running
                if len(self.running_workers) < self.max_workers:
                    self.log.debug("starting worker #{0}".format( self.threads_cre+1 ))
                    worker = Thread(target=self.sendToMysql(event_queue), 
                                    name=str(self.threads_cre+1))
                    self.running_workers.append(worker)
                    worker.start()
                    self.threads_cre += 1
                    # reset the timer so it does not interfere with the usual
                    # dumping of the event-data in the queue
                    self.ev_timer.reset()

                    # reset our queue to prevent duplicate entries
                    del event_queue[:]
                else:
                    # FIXME: we need to handle this situation somehow if
                    # too many workers are running. just flush the events?
                    self.log.critial("too many workers running, loosing data!!!")
                   
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
                    self.log.debug("joined worker #{0}".format(worker.getName()))
                    self.threads_join += 1

            # get rid of the old reference  and set a new one
            # FIXME: is this really neccessary?
            del self.running_workers

            self.running_workers = clean_workers
            self.events_rec += 1

            # we update the stats every 'received div handled == 0'
            # or if we recevied a timer event for our ResetTimer
            if( (self.events_rec % self.state_upd) == 0 ):
                self.writeState()
            elif(self.ev_timer_ev):
                self.writeState()
                self.ev_timer_ev = False

            if self.shutdown:
                break

        self.log.info("listen loop ended...")                
        self.stop()

    def status(self):
        pid = self.getPid()
        if( os.path.exists('/proc/' + str(pid))):
            try:
                data = self.getState()
                print "running with pid {0}".format(pid)
                print "events (handled/recv): {0}/{1}".format(data['events_handled'],
                                                              data['events_received']),
                print "threads (created/joined): {0}/{1}".format( data['threads_created'],
                                                                  data['threads_joined'])
            except Exception as e:
                self.log.critical("State in unknown format, cant print")
                self.log.exception(e)
                print "State in unknown format, cant print"
        else:
            self.log.critical("pidfile '{0}' not found. is the daemon running?".format(self.pidfile))



    def getPid(self):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
            return pid

        except IOError:
            return None

    def getState(self):
        data = FileReader().load(self.state_file)

        if( type(opts) is dict ):
            return data
        else:
            return "Failed to read state_file '{0}'".format(self.state_file)


    def writeState(self):
        try:
            # write the info to the specified log
            f = open(self.state_file, 'w')
            f.writelines( simplejson.dumps( {'events_received' : self.events_rec,
                                             'events_handled' : self.events_han,
                                             'threads_created' : self.threads_cre,
                                             'threads_joined' : self.threads_join}
                                          ))
            # if we have the same pid as the pidfile, we are the running daemon
            # and also print the current counters to the logfile with 'info'
            if( os.getpid() == self.pid ):
                self.log.info("running with pid {0}".format(self.pid))
                self.log.info("events (handled/recv): {0}/{1}".format(self.events_han,
                                                                      self.events_rec))
                self.log.info("threads (created/joined): {0}/{1}".format( self.threads_cre,
                                                                          self.threads_join))


            f.write("\n")
            f.close()
            sys.stdout.flush()
        except Exception as e:
            self.log.critical("Failed to write state, but no one can read me, what a pity")
            self.log.exception(e)
            pass

    # this is used to pass the mysql-credentials so
    # the threads can use on their own context
    def initMysql(self, **kwargs):
        self.mysql_set = kwargs

    # the method dumps the data into mysql. its always started
    # in its own thread and makes its own mysql-connection 
    def sendToMysql(self, qdata):

        # create the mysql connection and get the cursor
        conn = MysqlConn(**self.mysql_set)
        cursor = conn.getCursor()
        self.log.debug("created new mysql connection {0}".format(conn))

        # keep track of the queue_entries dumped
        dumped = 0

        # dump all the data we received depending on the type
        # currently there only is:
        # new_job > saltresults.command
        # jid > saltresults.results
        for entry in qdata:
            for key in self.event_struct.keys():
                if( self.event_struct[key]['tag'].match( entry['tag'] ) ):

                    try:
                        # create a shortcut to various data

                        # the sql_template
                        sql_qry = self.event_struct[key]['template']
                        # the dict to use for data from the event
                        src_dict = self.event_struct[key]['dict_name']
                        # the fields from src_dict we need
                        src_flds = self.event_struct[key]['fields']
                        # our data is on the first level
                        src_data = entry[src_dict]

                        # create some target vars
                        # the mysql-table toinsert into
                        tgt_table = self.event_struct[key]['mysql_tab']

                        # the data to format the query with. it is VERY IMPORTANT that the ORDER
                        # AND COUNT of the variables are preserved here. the fields-list and the template
                        # from the config are formatted with one another to form a very flexible sql-query. 
                        # the order in the fields- and template-variable have to match EXACTLY, otherwise
                        # the query will brake with an invalid syntax or end up with wrond data 
                        tgt_data = []

                        # create a list to format the sql_qry with, order 
                        # is very important here! to be on the safe side, return
                        # data is always converted to base64 and list-data always json
                        # dumped. the rest of the data is inserted as is
                        for fld in src_flds:
                            if( fld == 'return' ):
                                tgt_data.append( b64encode( simplejson.dumps( src_data[fld] ) ) )
                            else:
                                if( type(src_data[fld] ) is list ):
                                    tgt_data.append( simplejson.dumps( src_data[fld] ) ) 
                                else:
                                    tgt_data.append( src_data[fld] ) 

                        self.log.debug(sql_qry.format(tgt_table, *tgt_data ))

                        # execute the sql_qry
                        cursor.execute( sql_qry.format(tgt_table, *tgt_data) )
                        dumped += 1
                    except Exception as e:
                        self.log.critical("dont know how to handle: '{0}'".format(entry))
                        self.log.exception(e)
                        pass

        self.log.info("dumped {0} msgs into mysql".format(dumped))
        conn.comm()
        # explicitly close the connection
        conn.cls()
        self.log.debug("closed mysql connection {0}".format( conn ) )
        # ensure our current qdata is really empty
        del qdata[:]


    # this is used to tell the class about the events it should handle.
    # it has to be a dictionary with appropriate mappings in it. see the
    # config file for examples on how to compose the dict. each entry is
    # converted to a precompiled regex for maximum flexibility
    def initEvents(self, events={}):
        self.event_struct = events
        # we precompile all regexes
        for key in events.keys():
            # we compile the regex configured in the config
             self.event_struct[key]['tag'] = compile( events[key]['tag'] )

if __name__ == '__main__':

        listener = SaltEventsDaemon()
        if( sys.argv[1] == 'fg' ):
            listener.listen()
        else:
            print "\n\t action unknown, try one of start, stop, status, restart\n"
