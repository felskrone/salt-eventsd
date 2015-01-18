'''
this Worker takes care of 'new_job'-event-data generated on
salt-masters by using the salt-binary or the mqshell.

it takes care of the fields 'tgt' and 'arg', which might contain
characters that brake mysql-queries because of '-characters
'''

# import and setup logger first, so we can catch
# missing libraries on imports
import logging

log = logging.getLogger(__name__)

try:
    import simplejson
    from base64 import b64encode
    import MySQLdb
    from socket import gethostname
except ImportError as mis_lib:
    log.error('Failed to start worker: {0}'.format(mis_lib))
    log.exception(mis_lib)


class New_Job_Worker(object):
    '''
    takes care of dumping 'new_job'-event-data into the database
    '''

    # the settings for the mysql-server to use
    # it should be a readonly user
    creds = {}
    api_host = gethostname()
    name = "New_Job_Worker"
    thread_id = None

    def setup(self, thread_id, **kwargs):
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
            self.name,
            self.dumped,
            self.creds['hostname'],
        ))
        self.conn.cls()
        # log.debug("Worker '{0}' shut down".format(self.name))

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

            # there one event we want to ignore. it just contains
            # {
            #     'tag': 'new_job',
            #     'data': {
            #         'tgt_type': 'glob',
            #         'jid': '20140515142954787191',
            #         'tgt': 'wp001.webpack.hosteurope.de',
            #         '_stamp': '2014-05-15T14:29:54.787681',
            #         'user': 'root',
            #         'arg': [],
            #         'fun': 'test.ping',
            #         'minions': ['wp001.webpack.hosteurope.de']
            #     }
            # }

            # DEPRECATED SINCE SALT 2014.01
            # its used by salt internally so we skip it
            # if 'minions' in src_data:
            #     return

            # the mysql-table to insert into
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
                # the data is generated on salt-masters by using
                # salt or the mqshell with parameters

                # arg-data is considered unsafe and needs to be
                # json-dumped and base64 encoded
                if fld == 'arg':
                    tgt_data.append(
                        b64encode(
                            simplejson.dumps(
                                src_data[fld]
                            )
                        )
                    )
                # same goes for the tgt-field
                elif fld == 'tgt':
                    if type(src_data[fld]) is list:
                        tgt_data.append(','.join(src_data[fld]))
                    else:
                        tgt_data.append(src_data[fld])
                # the rest of the new_job-data can be inserted as is
                # because its usually ints, bool, simple strings
                else:
                    tgt_data.append(src_data[fld])

            # append the current api-host we'running on
            tgt_data.append(self.api_host)
            log.debug(self.thread_id + "# " + sql_qry.format(tgt_table, *tgt_data))

            # execute the sql_qry
            self.cursor.execute(sql_qry.format(tgt_table, *tgt_data))
            # commit the changes
            self.conn.comm()
            self.dumped += 1
        except Exception as excerr:
            log.critical("{0}# dont know how to handle:'{1}'".format(self.thread_id, event))
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
