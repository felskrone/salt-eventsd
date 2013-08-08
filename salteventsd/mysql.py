#!/usr/bin/python

import MySQLdb
import logging

class MysqlConn(object):

    def __init__(self,
                 **kwargs):
        self.cursor = None

        self.mysql_con = MySQLdb.connect(host=kwargs['host'],
                                         user=kwargs['username'], 
                                         passwd=kwargs['password'],
                                         db=kwargs['db'])
        self.cursor = self.mysql_con.cursor()

    def getCursor(self):
        return self.cursor
    def cls(self):
        self.mysql_con.close()
    def comm(self):
        self.mysql_con.commit()
