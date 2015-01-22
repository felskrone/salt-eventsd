'''
The loader is created by the main SaltEventsDaemon. It takes care of loading
the given config with a default of '/etc/salt/eventsd'. It also takes care of
initializing the logger from saltstack.
'''

import sys
import logging
import salt.log
import os
import yaml

logger = salt.log.setup.logging.getLogger(__name__)
log = logging.getLogger(__name__)


class SaltEventsdLoader(object):
    '''
    The loader takes care of reading the configfile and
    setting up the correct logger.
    '''
    def __init__(self, config=None, log_level=None, log_file=None, daemonize=False):
        self.config_file = config if config else "/etc/salt/eventsd"
        # retrieve current settings from the config file
        self.opts = None
        self._read_yaml(self.config_file)

        # make sure we have a 'general' section
        if 'general' in self.opts.keys():
            self.gen_opts = self.opts['general']

        # Use log level if explicitly set from cli
        if log_level:
            self.gen_opts['loglevel'] = log_level

        # Use log file if explicitly set from cli
        if log_file:
            self.gen_opts['logfile'] = log_file

        self.gen_opts['daemonize'] = daemonize

        self._init_logger()
        log.info("loaded config from {0}".format(config))

    def _init_logger(self):
        '''
        sets up the logger used throughout saltt-eventsd
        '''
        # make sure we have the required settings for our logging
        if ('logfile' in self.gen_opts) and \
           ('loglevel' in self.gen_opts):

            salt.log.setup_logfile_logger(
                self.gen_opts['logfile'],
                self.gen_opts['loglevel'],
            )

            # Only log to foreground if not running as a daemon
            if not self.gen_opts['daemonize']:
                salt.log.setup_console_logger(
                    log_level=self.gen_opts['loglevel'],
                )
        else:
            # if no log settings found, use defaults

            # Only log to foreground if not running as a daemon
            if not self.gen_opts['daemonize']:
                salt.log.setup_console_logger(
                    log_level="warn"
                )

            salt.log.setup_logfile_logger(
                '/var/log/salt/eventsd',
                'warn',
            )

    def getopts(self):
        '''
        returns the parsed options to the SaltEventsDaemon-Class
        '''
        return self.opts

    def _read_yaml(self, path):
        '''
        reads a yaml-formatted configuration file at the given path and
        returns a python dictionary with the pared items in it.
        '''
        try:
            yaml_handle = open(path)
            self.opts = yaml.load(yaml_handle.read())
        except yaml.parser.ParserError as yamlerr:
            print("Failed to parse configfile: {0}".format(path))
            print(yamlerr)
            sys.exit(1)
        except yaml.scanner.ScannerError as yamlerr:
            print("Failed to parse configfile: {0}".format(path))
            print(yamlerr)
            sys.exit(1)
        except IOError as ioerr:
            print("Failed to read configfile:")
            print(os.strerror(ioerr.errno))
            sys.exit(1)
        except OSError as oserr:
            print("Failed to read configfile:")
            print(os.strerror(oserr.errno))
            sys.exit(1)
