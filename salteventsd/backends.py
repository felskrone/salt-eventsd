import os
import imp
import re
import sys
import logging

log = logging.getLogger(__name__)

class BackendMngr(object):

    def __init__(self, be_dirs):
        self.be_dirs = be_dirs
        self.naming_scheme = "^[aA-zZ]+Worker.py$"
        self.backends = {}
        

    def listWorkers(self, directory):
        for root, subFolders, files in os.walk(directory):
            for filename in files:
                if( re.match(self.naming_scheme, filename) ):
                    new_plugin = self.loadPluginFromFile(filename)

    def loadPlugins(self):
        for path in self.be_dirs:
            self.listWorkers(path)
        return self.backends
        

    def loadPluginFromFile(self, filename):    
        (path, name) = os.path.split(filename)
        (name, ext) = os.path.splitext(name)

        # if we try to load a module from file, the module might be using import to import other libraries, for example
        # a WebpackLib.py. since we import a plugin by full-path-name which is usually NOT in the python-search-path,
        # a library would have to reside in the same directory as the plugin to be found. 
        # since we dont want various library-files (which essentially might do the same thing) scattered throughout the 
        # plugin-directories and certainly not in a python-search-path that has nothing to with the webpack-shell (like /usr/lib/python2.x)
        # we define one library-dir for job-plugins which we add to the python-search-path. if a job-plugin uses import
        # statements and trys to import a library, only the std-python-search-path, the plugins cwd and this library-path
        # are searched for that imported module. if it cant be found, the plugin is skipped
        for path in self.be_dirs:
            sys.path.insert(0, path)

        # look in the current search path for given module_name
        try:
            (file, filename, data) = imp.find_module(name, [path] )
            # load the module from file
            loaded_mod = imp.load_module(name, file, filename, data)
            log.info("loaded_mod: " + str(loaded_mod) )

            # make sure the expected class is found in the loaded file. this means the name of the file
            # we are importing must match the class-name in the file that is being imported (without .py). 
            # otherwise we would not know which class to import from the file. it may also contain various
            # other classes we dont need to know about
            if( hasattr(loaded_mod, name) ):
                plugin_class = getattr(loaded_mod, name)()
                log.info(plugin_class)
                self.backends[name] = plugin_class
            else:
                log.info("ERR0: file found but not loaded {0}".format(filename))

        except ImportError, i:
            log.exception(i)
            log.info("ERR1: file found but not loaded {0}".format(filename))

