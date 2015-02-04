'''
The loader is created by the main SaltEventsDaemon. It takes care of loading
the given config with a default of '/etc/salt/eventsd'. It also takes care of
initializing the logger from saltstack.
'''

# python std lib
import copy
import logging
import os
import sys
import yaml

# salt imports
from salt.log import setup_console_logger, setup_logfile_logger
from salt.log.setup import logging as salt_logging

logger = salt_logging.getLogger(__name__)
log = logging.getLogger(__name__)


class SaltEventsdLoader(object):
    '''
    The loader takes care of reading the configfile and
    setting up the correct logger.
    '''
    def __init__(self, config=None, log_level=None, log_file=None, daemonize=False):
        self.config_file = config if config else "/etc/salt/eventsd"

        # retrieve initial settings from the config file
        self.opts = self._read_yaml(self.config_file)

        # A 'general' section is required in the config
        if 'general' in self.opts:
            self.gen_opts = copy.deepcopy(self.opts['general'])
        else:
            raise Exception("No 'general' options found in config file: {0}".format(self.config_file))

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

            setup_logfile_logger(
                self.gen_opts['logfile'],
                self.gen_opts['loglevel'],
            )

            # Only log to foreground if not running as a daemon
            if not self.gen_opts['daemonize']:
                setup_console_logger(
                    log_level=self.gen_opts['loglevel'],
                )
        else:
            # if no log settings found, use defaults

            # Only log to foreground if not running as a daemon
            if not self.gen_opts['daemonize']:
                setup_console_logger(
                    log_level="warn"
                )

            setup_logfile_logger(
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
            with open(path) as stream:
                return yaml.load(stream)
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
