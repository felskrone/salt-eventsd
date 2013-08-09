#!/usr/bin/python
#
# A resettable timer to have an reoccuring event which can be canceled
#
import threading
import time
import sys 
import logging
import salt.log
from random import randint

log = logging.getLogger(__name__)

class ResetTimer(threading.Thread):

    running = False
    counter = 0

    def __init__(self, 
                 interval,
                 ref=False): 
        threading.Thread.__init__(self) 
        self.ref = ref
        self.interval = interval
 

    def run(self): 
        log.info("starting event_timer")
        self.running = True

        while self.running:

            self.counter = 0

            # run our loop until we hit out interval
            # the counter might get reset externally
            while self.counter < self.interval:
                self.counter += 1

                # if the timer was stopped, brake the loop
                if( self.running ):
                    time.sleep(1)
                else:
                    break

            # if set, call an external function
            if( self.ref ):
                self.ref.timerEvent()
            else:
                print "done"

    def reset(self):
        '''
        reset the current timer to zero
        '''
        log.info("resetting the timer")
        self.counter = 0

    def stop(self):
        '''
        stop the timer
        '''
        self.running = False

    def isRunning(self):
        '''
        check if the timer is still running
        '''
        return self.running



if __name__ == '__main__':
    try:
        t = Timer(20)
        t.start()
        k = 0
        stop = randint(1,20)
        while True:
            k += 1
            if(k == stop):
                t.reset()
                stop = randint(1,19)
                print "break next:", stop
                k = 0
            time.sleep(1)

    except KeyboardInterrupt as f:
        t.stop()
        t.join()
    print "exit"
