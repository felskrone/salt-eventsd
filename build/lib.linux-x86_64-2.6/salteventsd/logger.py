#!/usr/bin/python

import sys
import logging


class Logger(logging.FileHandler):

    def __init__(self,
                 name='',
                 logfile=False,
                 logfile_level='',
                 console=False,
                 console_level=None):

        self.logger = logging.getLogger(name)

        if( logfile ):
            self.setupLogfileLog(logfile,
                                 self.getLevel( logfile_level) )
        if( console ):
            self.setupConsoleLog(self.getLevel( console_level ))

    def getLevel(self, level):
        if( level == 'info' ):
            loglevel = logging.INFO
        elif( level == 'debug' ):
            loglevel = logging.DEBUG
        elif( level == 'critical' ):
            loglevel = logging.CRITICAL
        else:
            loglevel = logging.INFO
        return loglevel

    def setupLogfileLog(self,
                        logfile,
                        level):

        fh = logging.FileHandler(logfile)
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        fh.setFormatter(formatter)
        fh.setLevel( level )
        self.logger.addHandler(fh)

    def setupConsoleLog(self,
                        level):
        # define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(level)
        # set a format which is simpler for console use
        formatter = logging.Formatter('%(name)-8s: %(levelname)-8s: %(message)s')
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        self.logger.addHandler(console)
