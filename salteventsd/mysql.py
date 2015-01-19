'''
The Mysql-Backend for the SaltEventsDaemon. Its basically a wrapper
around a mysql-connection.
'''

import MySQLdb
import logging

log = logging.getLogger(__name__)


class MysqlConn(object):
    '''
    Mysql Wrapper class to create simple mysql-connections
    '''

    def __init__(self, **kwargs):
        '''
        creates a mysql connecton on invocation
        '''
        self.cursor = None

        try:
            self.mysql_con = MySQLdb.connect(
                host=kwargs['host'],
                user=kwargs['username'],
                passwd=kwargs['password'],
                db=kwargs['db'],
            )
            self.cursor = self.mysql_con.cursor()
        except MySQLdb.MySQLError as sqlerr:
            log.error("Conneting to the mysql-server failed:")
            log.error(sqlerr)
        log.debug("initialized connection {0}".format(self))

    def get_cursor(self):
        '''
        returns the current mysql-cursor for this connection
        '''
        log.debug("returning cursor")
        if self.cursor:
            return self.cursor
        else:
            raise AttributeError("Trying to get cursor of uninitialized connection")

    def cls(self):
        '''
        explicitly close a connection tomysql
        '''
        log.debug("closing connection {0}".format(self))

        if self.mysql_con:
            self.mysql_con.close()
        else:
            raise AttributeError("Trying close uninitialized connection")

    def comm(self):
        '''
        commits the changes of the connectionexplicitly close a connection tomysql
        '''
        self.mysql_con.commit()
