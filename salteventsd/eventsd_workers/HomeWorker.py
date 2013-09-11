'''
This is the main SaltEventsDaemon class. It holds all the logic that listens 
for events, collects events and starts all the workers to dump data.
'''

import simplejson
import threading
from base64 import b64encode
import logging
import MySQLdb

log = logging.getLogger(__name__)

class HomeWorker(object):
    '''
    A MysqlWorker for the salt-eventsd. It starts a mysql connection,
    pumps all events it receives according to their config in to the
    desired tables and finally disconnects from the mysql-server
    '''

    # the settings for the mysql-server to use
    username = "collector"
    password = "Ahpoohah3shupaiz1ooj"
    database = "saltresults"
    hostname = "localhost"

    name = "HomeWorker"

    def setup(self):
        '''
        init the connection and do other necessary stuff
        '''
        # create the mysql connection and get the cursor

        self.conn = MysqlConn(self.hostname,
                              self.username,
                              self.password,
                              self.database)

        self.cursor = self.conn.get_cursor()

        # keep track of the events dumped
        self.dumped = 0

        log.info("Worker '{0}' initiated".format(self.name))

    
    def shutdown(self):
        '''
        close the connection to the mysql-server and maybe
        do some other cleanup if necessary
        '''
        log.info("dumped {0} events to {1}".format(self.dumped,
                                                   self.hostname))
        self.conn.cls()
        log.debug("Worker '{0}' shut down".format(self.name))
           

    def send(self, 
             entry,
             event_set):
        '''
        this has to be present in any Worker for the salt-eventsd.
        It receives events with their corresponding setting and 
        passes it on to a handler-function
        '''
        log.debug("received entry:{0} with settings: {1}".format(entry,
                                                                 event_set))
        if self.cursor:
            self._store(entry, event_set)
        else:
            log.error("No connection available, event ignored!")
            return


    def _store(self,
               event,
               event_set):
        '''
        the actual worker-function which arses the event-configuration,
        tries to match it against the event and creates a mysql-query 
        which it finally executes to send the data to mysql
        '''

        try:
            # the sql_template
            sql_qry = event_set['template']
            # the dict to use for data from the event
            src_dict = event_set['dict_name']
            # the fields from src_dict we need
            src_flds = event_set['fields']
            # our data is on the first level
            src_data = event[src_dict]

            # the mysql-table toinsert into
            tgt_table = event_set['mysql_tab']

            # the data to format the query with. it is IMPORTANT
            # that the ORDER AND COUNT of the variables is preserved
            # here. the fields-list and the template from the config
            # are formatted with one another to form a very flexible
            # sql-query. the order in the fields- and template-
            # variable have to match EXACTLY, otherwise the query 
            # will brake with an invalid syntax or maybe just end up
            # with wrong data 
            tgt_data = []

            # create a list to format the sql_qry with, order 
            # is very important here! to be on the safe side, return
            # data is always converted to base64 and listdata always
            # json-dumped. the rest of the data is inserted as is
            for fld in src_flds:
                if( fld == 'return' ):
                    tgt_data.append(b64encode( 
                                        simplejson.dumps(
                                            src_data[fld])
                                        )
                                   )
                else:
                    if( type(src_data[fld] ) is list ):
                        tgt_data.append(simplejson.dumps( 
                                            src_data[fld])
                                       ) 
                    else: 
                        tgt_data.append(src_data[fld]) 

            log.debug(sql_qry.format(tgt_table, 
                                     *tgt_data))

            # execute the sql_qry
            self.cursor.execute( sql_qry.format(tgt_table, 
                                           *tgt_data) )
            # commit the changes
            self.conn.comm()
            self.dumped += 1
        except Exception as excerr:
            log.critical("dont know how to handle:'{0}'".format(
                                                            event)
                                                         )
            log.exception(excerr)


class MysqlConn(object):
    ''' 
    Mysql Wrapper class to simply create mysql-connections
    '''

    def __init__(self,
                 hostname,
                 username,
                 password,
                 database):
        ''' 
        creates a mysql connecton on invocation
        '''
        self.username = username
        self.password = password
        self.database = database
        self.hostname = hostname
        self.cursor = None

        try:
            self.mysql_con = MySQLdb.connect(host = self.hostname,
                                             user = self.username,
                                             passwd = self.password,
                                             db = self.database)
            self.cursor = self.mysql_con.cursor()

        except MySQLdb.MySQLError as sqlerr:
            self.mysql_con = False
            log.error("Conneting to the mysql-server failed:")
            log.error(sqlerr)
        else:
            log.debug("initialized connection {0}".format(self))

    def get_cursor(self):
        ''' 
        returns the current mysql-cursor for this connection
        '''
        if( self.cursor ):
            return self.cursor
        else:
            return None

    def cls(self):
        ''' 
        explicitly close a connection tomysql
        '''
        log.debug("closing connection {0}".format(self))

        if( self.mysql_con ):
            self.mysql_con.close()

    def comm(self):
        ''' 
        commits the changes of the connectionexplicitly close a connection tomysql
        '''
        self.mysql_con.commit()
