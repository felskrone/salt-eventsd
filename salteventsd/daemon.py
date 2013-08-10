'''
this daemon is based on the work of Sander Marechal
http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/

Its extended with a signal handler so debians start-stop-daemon can be used. 
That change also cleans up the code because stop() and restart() can be 
removed/shortened. It has also been updated to newer python versions
and python code styles.
'''

import sys
import os
import signal
import logging

log = logging.getLogger(__name__)
 
class Daemon(object):
    '''
    daemonizing class that does all the double-forking magic 
    '''

    def __init__(self, 
                 pidfile, 
                 stdin='/dev/null', 
                 stdout='/dev/null', 
                 stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def stop(self,
             signal,
             frame):
        '''
        stop the daemon and clean up the pidfile
        '''
        self.delpid()
        # we call os._exit here, because sys.exit() only raises an exception
        # and if you're in a try:except-block the exception will be caught
        os._exit(0)

    def daemonize(self):
        '''
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        '''
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, oserr:
            sys.stderr.write("fork #1 failed:{0}({1})\n".format(oserr.errno, 
                                                                oserr.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, oserr:
            sys.stderr.write("fork #2 failed:{0}({1})\n".format(oserr.errno, 
                                                                oserr.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        stdi = file(self.stdin, 'r')
        stdo = file(self.stdout, 'a+')
        stde = file(self.stderr, 'a+', 0)
        os.dup2(stdi.fileno(), sys.stdin.fileno())
        os.dup2(stdo.fileno(), sys.stdout.fileno())
        os.dup2(stde.fileno(), sys.stderr.fileno())

        # register two signal handlers to handle SIGTERM and SIGKILL properly
        signal.signal(signal.SIGINT,  self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        # write pidfile
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)

    def delpid(self):
        '''
        remove our pidfile on shutdown
        '''
        os.remove(self.pidfile)

    def start(self):
        '''
        Start the daemon
        '''
        # Check for a pidfile to see if the daemon already runs
        try:
            pidf = file(self.pidfile,'r')
            pid = int(pidf.read().strip())
            pidf.close()
        except IOError:
            pid = None

        if pid:
            sys.stderr.write("pidfile {0} already exists.\n".format(self.pidfile))
            sys.exit(1)
       
        # Start the daemon
        self.daemonize()
        self.run()


    def run(self):
        '''
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        '''
