'''
this Worker takes care of return-data being returned by a minion.
it takes care of dumping the 'return'-field into the database
after its json-encoded and base64 converted.
'''

# import and setup logger first, so we can catch
# missing libraries on imports
import logging

log = logging.getLogger(__name__)

try:
    import simplejson as json
except ImportError:
    import json

try:
    from base64 import b64encode
    import MySQLdb
except ImportError as mis_lib:
    log.error('Failed to start worker: {0}'.format(mis_lib))
    log.exception(mis_lib)


class Minion_Return_Worker(object):
    '''
    takes care of dumping 'return'-data into the database
    '''
    # the settings for the mysql-server to use
    creds = {}
    name = "Minion_Return_Worker"
    thread_id = None

    def setup(self,
              thread_id,
              **kwargs):
        '''
        init the connection and do other necessary stuff
        '''
        self.thread_id = thread_id

        # get the credentials from the main config in kwargs
        if 'worker_credentials' in kwargs:
            if self.name in kwargs['worker_credentials']:
                self.creds.update(kwargs['worker_credentials'][self.name])
            elif 'all' in kwargs['worker_credentials']:
                self.creds.update(kwargs['worker_credentials']['all'])
            else:
                log.info('{0}# no credentials loaded from config'.format(self.thread_id))

        # create the mysql connection and get the cursor
        self.conn = MysqlConn(
            self.creds['hostname'],
            self.creds['username'],
            self.creds['password'],
            self.creds['database'],
            self.thread_id,
        )

        self.cursor = self.conn.get_cursor()

        # keep track of the events dumped
        self.dumped = 0

        log.info("{0}# Worker '{1}' initiated".format(self.thread_id, self.name))

    def shutdown(self):
        '''
        close the connection to the mysql-server and maybe
        do some other cleanup if necessary
        '''
        log.info("{0}# dumped {1} events to {2}".format(
            self.thread_id,
            self.dumped,
            self.creds['hostname']
        ))
        self.conn.cls()

    def send(self, entry, event_set):
        '''
        this has to be present in any Worker for the salt-eventsd.
        It receives events with their corresponding setting and
        passes it on to a handler-function
        '''
        # log.debug("received entry:{0} with settings: {1}".format(entry, event_set))
        self._store(entry, event_set)

    def _store(self, event, event_set):
        '''
        the actual worker-function which parses the event-configuration,
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

            # there is one event we want to ignore. it just contains
            # 'tag': '20140228142919397750',
            # 'data':{
            #          '_stamp': '2014-02-28_14:29:19.398033',
            #          'minions': ['wp033.webpack.hosteurope.de']
            #        }
            # its used by salt internally so we skip it. we never get a return
            # that has 'minions' in it unless we put it in there ourselves
            if 'minions' in src_data:
                return

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
                # the 'return'-field is ALWAYS json-dumped and base64-
                # converted. its data is returned from a minion and can
                # never ever be "trusted"
                if fld == 'return':
                    tgt_data.append(
                        b64encode(
                            json.dumps(
                                src_data[fld]
                            )
                        )
                    )
                # all other fields should be safe to insert
                else:
                    tgt_data.append(src_data[fld])

            log.debug(self.thread_id + "# " + sql_qry.format(tgt_table, *tgt_data))

            # execute the sql_qry
            self.cursor.execute(sql_qry.format(tgt_table, *tgt_data))
            # commit the changes
            self.conn.comm()
            self.dumped += 1
        except Exception as excerr:
            log.critical("{0}# dont know how to handle:'{1}'".format(
                self.thread_id,
                event,
            ))
            log.exception(excerr)


class MysqlConn(object):
    '''
    Mysql Wrapper class to simply create mysql-connections
    '''

    def __init__(self, hostname, username, password, database, thread_id):
        '''
        creates a mysql connecton on invocation
        '''
        self.username = username
        self.password = password
        self.database = database
        self.hostname = hostname
        self.cursor = None
        self.thread_id = thread_id

        try:
            self.mysql_con = MySQLdb.connect(
                host=self.hostname,
                user=self.username,
                passwd=self.password,
                db=self.database,
            )
            self.cursor = self.mysql_con.cursor()
        except MySQLdb.MySQLError as sqlerr:
            log.error("{0}# Connecting to the mysql-server failed:".format(self.thread_id))
            log.error(sqlerr)
        # log.debug("initialized connection {0}".format(self))

    def get_cursor(self):
        '''
        returns the current mysql-cursor for this connection
        '''
        if self.cursor:
            return self.cursor
        else:
            raise AttributeError("Trying to get cursor of uninitialized connection")

    def cls(self):
        '''
        explicitly close a connection tomysql
        '''
        # log.debug("closing connection {0}".format(self))
        if self.mysql_con:
            self.mysql_con.close()
        else:
            raise AttributeError("Trying close uninitialized connection")

    def comm(self):
        '''
        commits the changes of the connectionexplicitly close a connection tomysql
        '''
        self.mysql_con.commit()
