#!/usr/bin/python
#

import threading
import time
import sys 
import logging
from random import randint


class ResetTimer(threading.Thread):

    running = False
    counter = 0
    

    def __init__(self, 
                 interval,
                 ref=False): 
        threading.Thread.__init__(self) 
        self.ref = ref
        self.interval = interval
        self.log = logging.getLogger('mqevents')
 

    def run(self): 
        self.log.info("starting event_timer")
        self.running = True

        while self.running:

            self.counter = 0

            while self.counter < self.interval:
                self.counter += 1

                if( self.running ):
                    time.sleep(1)
                else:
                    break

            if( self.ref ):
                self.ref.timerEvent()
            else:
                print "done"

    def reset(self):
        # FIXME: the timer needs to be resettable
        self.log.info("resetting the timer")
        self.counter = 0

    def stop(self):
        self.running = False

    def isRunning(self):
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
