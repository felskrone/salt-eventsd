#/usr/bin/env python

#
# this daemon is based on the work of Sander Marechal
# http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#
# its extended with a signal handler so start-stop-daemon can be used. that change
# also cleans up the code because stop() and restart() can be removed/shortened
import sys, os, time, atexit
import signal
 
class Daemon(object):
    '''
    A generic daemon class.
    
    Usage: subclass the Daemon class and override the run() method
    '''

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def stop(self,
             signal,
             frame):
        self.delpid()
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
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
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
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

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
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
       
        # Start the daemon
        self.daemonize()
        self.run()


    def run(self):
        '''
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        '''
