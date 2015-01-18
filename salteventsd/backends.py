'''
fusel
'''
import os
import imp
import re
import sys
import logging

log = logging.getLogger(__name__)


class BackendMngr(object):
    '''
    Loads classes from python-files named "^[aA-zZ]+Worker.py$" from the
    backends-directory (default: /etc/salt/eventsd_workers)
    '''

    def __init__(self, be_dirs):
        self.be_dirs = be_dirs
        self.naming_scheme = "^[aA-zZ]+Worker.py$"
        self.backends = {}

    def list_workers(self, directory):
        '''
        lists files matching the naming_schema of the workers and loads
        the class from them by trying to load a class named
        <filename_without_extension> from it
        '''
        for root, subFolders, files in os.walk(directory):
            for filename in files:
                if re.match(self.naming_scheme, filename):
                    self.load_plugin_from_file(filename)

    def load_plugins(self):
        '''
        wrapper-function for list_workers()
        '''
        for path in self.be_dirs:
            self.list_workers(path)
        return self.backends

    def load_plugin_from_file(self, filename):
        '''
        loads a class from a file name by trying to load a class
        named like the given filename without extension
        '''
        (path, name) = os.path.split(filename)
        (name, ext) = os.path.splitext(name)

        # insert the paths defined in the be_dirs into our path-variable
        for path in self.be_dirs:
            sys.path.insert(0, path)

        # look in the current search path for the given module_name
        try:
            (file_n, filename, data) = imp.find_module(name, [path])
            # load the module from file
            loaded_mod = imp.load_module(name, file_n, filename, data)
            log.info("loaded_mod: " + str(loaded_mod))

            # make sure the expected class is found in the loaded file. this
            # means the name of the file we are importing must match the class-
            # name in the file that is being imported (without .py). otherwise
            # we would not know which class to import from the file. it may
            # also contain various other classes we dont need to know about
            if hasattr(loaded_mod, name):
                plugin_class = getattr(loaded_mod, name)()
                log.info(plugin_class)
                self.backends[name] = plugin_class
            else:
                log.error("'{0}' found but class '{1}' not found in" + \
                          "file.".format(filename, name))

        except ImportError, i:
            log.exception(i)
            log.info("ERR1: file found but not loaded {0}".format(filename))
