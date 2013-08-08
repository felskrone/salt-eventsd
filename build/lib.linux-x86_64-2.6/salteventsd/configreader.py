#!/usr/bin/python

import os
import simplejson
import sys
import logging
from salteventsd.logger import Logger

class Configreader():
    '''
    read the json config into a dict and return it
    '''
    def __init__(self):

        # init logging with the desired loglevel
        # as soon as possible
        Logger( name='salt-eventsd',
                logfile='/var/log/salt/eventsd.log',
                logfile_level='debug',
                console=True,
                console_level='debug')

        self.log = logging.getLogger('salt-eventsd')


    def load(self, path):
        if( os.path.isfile(path) and ( os.path.getsize(path) > 0) ): 
            return self.readJSON(path)
        else:
            self.log.info("File '{0}' does not exist or is 0 bytes".format(path))
            sys.exit(1)


    def readJSON(self, path):
        try:
            json_handle = open(path)
            json_obj = simplejson.loads(json_handle.read())

        except simplejson.JSONDecodeError as jsonErr:
            self.log.critical("Failed to parse configfile: {0}".format(path))
            self.log.critical(jsonErr)
            sys.exit(1)

        except IOError as i:
            self.log.critical("Failed to read configfile:")
            self.log.critical( os.strerror(i.errno) )
            sys.exit(1)

        except OSError as o:
            self.log.critical("Failed to read configfile:")
            self.log.critical( os.strerror(o.errno) )
            sys.exit(1)

        return json_obj
