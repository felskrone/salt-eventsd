'''
A timer class that starts with an initial value and fires an event to
the reference given every time the timer-interval is reached. While
running, the timer-counter be be reset to start from the beginning.
'''

import threading
import time
import logging

log = logging.getLogger(__name__)


class ResetTimer(threading.Thread):
    '''
    A Resettable Timer Class
    '''
    running = False
    counter = 0

    def __init__(self, interval, ref=False, name='Noname'):
        threading.Thread.__init__(self)
        self.interval = interval
        self.ref = ref
        self.name = name

    def run(self):
        log.info("Starting {0}-timer".format(self.name))
        self.running = True

        while self.running:
            self.counter = 0

            # run our loop until we hit out interval
            # the counter might get reset externally
            while self.counter < self.interval:
                self.counter += 1

                # while we're running, sleep...
                if self.running:
                    time.sleep(1)
                # if the timer was stopped, brake the loop
                else:
                    break

            # if the reference is set, call it
            if self.ref:
                log.debug("{0}-timer finished, calling reference".format(self.name))
                self.ref.timer_event(self.name)
            else:
                log.debug("{0}-timer finished".format(self.name))

    def reset(self):
        '''
        reset the timer instance's counter (i.e. restart the loop)
        '''
        log.debug("resetting the {0}-timer".format(self.name))
        self.counter = 0

    def stop(self):
        '''
        stop the timer
        '''
        self.running = False

    def is_running(self):
        '''
        check if the timer is still running
        '''
        return self.running
