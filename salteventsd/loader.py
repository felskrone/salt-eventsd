#!/usr/bin/python

import sys
import logging
import salt.log
import os
import yaml

logger = salt.log.logging.getLogger(__name__)
log = logging.getLogger(__name__)


class SaltEventsdLoader(object):

    def __init__(self,
                 config='/etc/salt/eventsd'):

        self.opts = self.readYAML(config)

        log.info("loaded config from {0}".format(config))

        if 'general' in self.opts.keys():
            self.gen_opts = self.opts['general']

        self.initLogger()

    def initLogger(self):
        if ('logfile' in self.gen_opts) and \
           ('loglevel' in self.gen_opts) : 

            salt.log.setup_logfile_logger(self.gen_opts['logfile'],
                                     self.gen_opts['loglevel'])

        else:
            log.setup_logfile_logger('/var/log/salt/eventsd',
                                     'warn')

    def getopts(self):
        return self.opts


    def readYAML(self, path):
        try:
            yaml_handle = open(path)
            return yaml.load(yaml_handle.read())

        except yaml.parser.ParserError as yamlErr:
            log.critical("Failed to parse configfile: {0}".format(path))
            log.critical(yamlErr)
            sys.exit(1)

        except IOError as i:
            log.critical("Failed to read configfile:")
            log.critical( os.strerror(i.errno) )
            sys.exit(1)

        except OSError as o:
            log.critical("Failed to read configfile:")
            log.critical( os.strerror(o.errno) )
            sys.exit(1)
