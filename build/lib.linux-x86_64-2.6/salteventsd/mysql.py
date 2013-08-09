#!/usr/bin/python

import MySQLdb
import logging

class MysqlConn(object):

    def __init__(self,
                 **kwargs):

        '''
        creates a mysql connecton on invocation
        '''
        self.cursor = None

        self.mysql_con = MySQLdb.connect(host=kwargs['host'],
                                         user=kwargs['username'], 
                                         passwd=kwargs['password'],
                                         db=kwargs['db'])
        self.cursor = self.mysql_con.cursor()

    def getCursor(self):
        '''
        returns the current mysql-cursor for this connection
        '''
        return self.cursor

    def cls(self):
        '''
        explicitly close a connection tomysql
        '''
        self.mysql_con.close()

    def comm(self):
        '''
        commit our current changes to the mysql-server
        '''
        self.mysql_con.commit()
