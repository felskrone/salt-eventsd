'''
this Stat_Worker takes care of pushing statistical data into a backend,
in this case a mysql-backend with a table called events_stats.
'''

# import and setup logger first, so we can catch
# missing libraries on imports
import logging

log = logging.getLogger(__name__)

try:
    import threading
    import logging
    import MySQLdb
    from socket import gethostname
except ImportError as mis_lib:
    log.error('Failed to start worker: {0}'.format(mis_lib))
    log.exception(mis_lib)


class Stat_Worker(object):
    '''
    takes care of dumping statistical data into mysql
    '''

    # the settings for the mysql-server to use
    # it should be a readonly user
    creds = {}

    api_host = gethostname()

    name = "Stat_Worker"
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
        self.conn = MysqlConn(self.creds['hostname'],
                              self.creds['username'],
                              self.creds['password'],
                              self.creds['database'],
                              self.thread_id)

        self.cursor = self.conn.get_cursor()

        log.info("{0}# {1} initiated".format(self.thread_id, self.name))


    def shutdown(self):
        '''
        close the connection to the mysql-server and maybe
        do some other cleanup if necessary
        '''
        log.info("{0}# dumped statistics to {1}".format(self.name,
                                                        self.creds['hostname']))
        self.conn.cls()


    def send(self,
             stats_data,
             dummy=None):
        '''
        This is the main entry-point for the salt-eventsd daemon
        to send data to the Stat_Worker. The Format of the events
        is always a dict with various counters collected by the daemon.

        For now the valid keys are:
        { 
            "events_hdl": <int>, 
            "threads_joined": <int>, 
            "threads_created": <int>, 
            "events_rec": <int>, 
            "events_hdl_sec": <float>, 
            "events_tot_sec": <float>
        }

        If you derive your Stat_Worker from this example, i advise to always
        dump the data first, and see what you get.  There might be even more
        key:value pairs in the future.
        
        Note that dummy is just that, a dummy variable and will always be None.
        Its just their to keep the daemon code clean and the workers alike.
        '''
        self._store(stats_data)


    def _store(self, stats_data):
        '''
        Sends the data to the mysql-server to insert them into the stats-table
        '''
        try:

            # the mysql-table to insert into
            qry = "INSERT INTO {0} (master, events_hdl, threads_joined, threads_created, events_rec, events_hdl_sec, events_tot_sec, last) "
            qry += "VALUES  ('{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', now()) "
            qry += "ON DUPLICATE KEY UPDATE "
            qry += "events_hdl='{2}', threads_joined='{3}', threads_created='{4}', events_rec='{5}', events_hdl_sec='{6}', events_tot_sec='{7}', last=now();"

            qry = qry.format(
                self.creds['table'],
                self.api_host,
                stats_data['events_hdl'],
                stats_data['threads_joined'],
                stats_data['threads_created'],
                stats_data['events_rec'],
                stats_data['events_hdl_sec'],
                stats_data['events_tot_sec']
            )

            # execute the sql_qry
            self.cursor.execute(qry)
            self.conn.comm()
        except Exception as excerr:
            log.critical("{0}# dont know how to handle:'{1}'".format(self.thread_id,
                                                                     stats_data))
            log.exception(excerr)

class MysqlConn(object):
    '''
    Mysql Wrapper class to simply create mysql-connections
    '''

    def __init__(self,
                 hostname,
                 username,
                 password,
                 database,
                 thread_id):
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
            self.mysql_con = MySQLdb.connect(host = self.hostname,
                                             user = self.username,
                                             passwd = self.password,
                                             db = self.database)
            self.cursor = self.mysql_con.cursor()
        except MySQLdb.MySQLError as sqlerr:
            log.error("{0}# Connecting to the mysql-server failed:".format(self.thread_id))
            log.error(sqlerr)
        #log.debug("initialized connection {0}".format(self))

    def get_cursor(self):
        '''
        returns the current mysql-cursor for this connection
        '''
        if(self.cursor):
            return self.cursor
        else:
            raise AttributeError("Trying to get cursor of uninitialized connection")

    def cls(self):
        '''
        explicitly close a connection tomysql
        '''
        #log.debug("closing connection {0}".format(self))

        if(self.mysql_con):
            self.mysql_con.close()
        else:
            raise AttributeError("Trying close uninitialized connection")

    def comm(self):
        '''
        commits the changes of the connectionexplicitly close a connection tomysql
        '''
        self.mysql_con.commit()
