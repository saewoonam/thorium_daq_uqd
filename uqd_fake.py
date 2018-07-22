import numpy as np
import time

class CTimeTag():
    def __init__(self):
        print('initialize fake CTimeTag')
        self.channels = 16
        self.lasttime = 0
        self.status = False

    def get_no_inputs(self):
        return self.channels

    def open(self):
        print('open timetag')

    def read():
        ch = np.random.randint(1,17, self.N, dtype=np.uint8)
        t = np.random.randint(0, 1000, self.N, dtype = np.uint64)
        t = t.cumsum() + self.lasttime
        self.lasttime = t[-1]
        time.sleep(1)
        return (ch, t)

    def start():
        self.status = True

    def stop():
        self.status = False

    def status():
        return self.status
