'''
This is the main SaltEventsDaemon class. It holds all the logic that listens 
for events, collects events and starts all the workers to dump data.
'''

import simplejson
import threading
from base64 import b64encode
import logging
from salteventsd.mysql import MysqlConn

log = logging.getLogger(__name__)

class SaltEventsWorker(threading.Thread):
    '''
    The worker for the salt-eventsd that pumps the data to the desired backend
    '''

    def __init__(self,
                 data,
                 name,
                 creds):
        threading.Thread.__init__(self)
        super(SaltEventsWorker, self).setName(name)
        log.info("worker {0} started".format(threading.currentThread().getName()))

        self.events = data
        self.mysql_set = creds

    def run(self):
        self._store_data(self.events)


    # the method dumps the data into mysql. its always started
    # in its own thread and makes its own mysql-connection 
    def _store_data(self, qdata):
        '''
        write a collection of events to the database. every invocation of
        this methoed creates its own thread that writes into the database
        '''

        # create the mysql connection and get the cursor
        conn = MysqlConn(**self.mysql_set)
        cursor = conn.get_cursor()

        # keep track of the queue_entries dumped
        dumped = 0

        # dump all the data we have received depending on the type
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
                        cursor.execute( sql_qry.format(tgt_table, 
                                                       *tgt_data) )
                        dumped += 1
                    except Exception as excerr:
                        log.critical("dont know how to handle:'{0}'".format(
                                                                        entry)
                                                                     )
                        log.exception(excerr)

        log.info("dumped {0} events".format(dumped))
        # commit and close the connection
        conn.comm()
        conn.cls()
        # ensure our current qdata is really empty
        del qdata[:]
