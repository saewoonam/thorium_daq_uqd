import shm
import ring
import numpy as np
import time
import logging
import logzero
import os.path
from logzero import logger


logzero.loglevel(logging.INFO)


class Buffer(object):
    def __init__(self, buffer_number= -1, size=100):
        # create = False
        # try:
        #     self._ch = shm.connect('ch')
        # except ValueError as e:
        #     logger.debug('ch does not exist, create new stuff')
        #     logger.debug('%r' % e)
        #     create = True
        if os.path.isfile('/dev/shm/ch'):  # create:
            self.connect()
        else:
            print('create new')
            self.new(size=size)
        # self.cmd = CmdBuffer()
 
    def connect(self):
        print('Try to connect')
        self._ch = shm.connect('ch')
        self._t = shm.connect('t')
        self.ch = ring.RingArray(self._ch)
        self.t = ring.RingArray(self._t)
        self.size = len(self._ch)
        self.indices = shm.connect('indices')
        self.realtime = shm.connect('realtime')
        self.number_channels = shm.connect('number_channels')

    # This is stuff to make it compatible with old ttag code
    # Need to add the following properties:
    #    datapoints
    #    channels
    #
    # Need the methods:  These are a hack because they don't
    #    do anything unless there is a cmd processor
    #
    #    start
    #    stop
    #
    @property  # property datapoints to mimic ttag package
    def datapoints(self):
        return self.indices[1]

    @property  # property channels to mimic ttag package
    def channels(self):
        return self.number_channels[0]
    @channels.setter  # setter for channels
    def channels(self, channels):
        self.number_channels[0] = channels

    def start(self):
        print('start not implemented, need to override this')
        # self.cmd.write('unpause')

    def stop(self):
        print('start not implemented, need to override this')
        # self.cmd.write('pause')

    def new(self, size=100):
        self.clean()
        self._ch = shm.new('ch', size, dt=np.uint8)
        self._t = shm.new('t', size, dt=np.uint64)
        self.ch = ring.RingArray(self._ch)
        self.t = ring.RingArray(self._t)
        self.size = size
        self.indices = shm.new('indices', 2, dt=np.int64)
        self.indices[0] = -size  # index 0: oldest valid timetag
        self.indices[1] = 0  # index 1: next time tag
        self.realtime = shm.new('realtime', 1, dt=np.double)
        self.number_channels = shm.new('number_channels', 1, dt=np.uint64)

    def clean(self):
        for name in ['ch', 't', 'indices', 'realtime', 'number_channels']:
            try:
                shm.rm(name)
            except:
                pass

    def add(self, ch, t):
        if type(ch) is np.ndarray:
            self.addarray(ch, t)
        elif type(ch) is list:
            self.addarray(ch, t)
        else:
            self.addarray([ch], [t])

    def addarray(self, ch, t):
        self.indices[0] = self.indices[0] + len(ch)
        self.ch.add(ch)
        self.t.add(t)
        self.indices[1] = self.indices[1] + len(ch)
        self.realtime[0] = time.time()

    def __del__(self):
        print('running __del__, is this intended?')
        # self.clean()
        pass

    def __getitem__(self, items):
        # print(type(items), items)
        if isinstance(items, (int, long, np.integer)):
            minindex = max(0, self.indices[0])
            maxindex = self.indices[1]
            if items>=0:  # Use absolute index number
                if items < minindex:
                    raise ValueError("index [%d] not valid, too small, min=%d" %
                            (items, minindex))
                if items > maxindex:
                    raise ValueError("index [%d] not valid, too big, min=%d" %
                            (items, maxindex))
                else:
                    index = items % self.size
            else:  #  items is negative, index relative to end
                index = maxindex + items
                # print('index', index, 'min', minindex, 'max', maxindex)
                if index < minindex:
                    print(items)
                    print('index', index, 'min', minindex, 'max', maxindex)
                    print('index', index, 'min', minindex, 'max', maxindex)
                    raise ValueError("index out of range, not between min and max")
                else:
                    index = index % self.size
            ch = self.ch[index]
            t = self.t[index]
        elif type(items) is slice:
            start = items.start
            stop = items.stop
            step = items.step
            minindex = max(0, self.indices[0])
            maxindex = self.indices[1]
            if (start):
                if (start < 0):
                    if (maxindex + start < minindex):
                        raise ValueError("start index out of buffer bounds")
                    start = maxindex + start
                else:
                    if (start >= maxindex
                            or start < minindex):
                        raise ValueError("start index out of buffer bounds")
            else:
                if (maxindex > self.size):
                    start = minindex
                else:
                    start = 0

            if (stop):
                if (stop < 0):
                    if (maxindex + stop < minindex):
                        raise ValueError("stop index out of buffer bounds")
                    stop = maxindex + stop
                else:
                    if (stop >= maxindex or stop < minindex):
                        raise ValueError("stop index out of buffer bounds")
            else:
                stop = maxindex
            # print('start', start, 'stop', stop)

            # if (stop < start):
            #     raise ValueError("Array indexing invalid")
            # elif (stop == start):
            #     return (numpy.array([], dtype=numpy.uint8), numpy.array(
            #         [], dtype=numpy.double))

            if (step):
                idx = np.arange(start, stop, step) % self.size
            else:
                idx = np.arange(start, stop) % self.size
            ch = self.ch[idx]
            t = self.t[idx]

            ch = np.copy(ch)
            t = np.copy(t)

        return (ch, t)

    def valid(self, index):
        return True if ((self[index][0] < 17) and (self[index][0]>=0)) else False

    def find_idx(self, left, right, stopbin):
        while (right - left) > 1:
            temp = int(np.floor((left + right) / 2))
            # print 'find_idx', left, right, temp 
            if not self.valid(temp):
                # First try decreasing temp until valid
                temp2 = temp
                while not self.valid(temp2):
                    temp2 = temp2 - 1
                if temp2 != left:  #  Did not find left limit
                    temp = temp2
                else:  # found left limit, increment temp
                    temp2 = temp
                    while not self.valid(temp2):
                        temp2 = temp2 + 1
                    if temp2 == right:  # found right limit, no valid timestamps between limits
                        break
                    else:
                        temp = temp2
            if self[temp][1] < stopbin:
                # print times[temp], stopbin, 'left'
                left = temp
            else:
                # print times[temp], stopbin, 'right'
                right = temp

            # print(left, right,  times[left], times[right], stopbin)

        return right


    def singles(self, deltat=1, resolution=1. / 6.4e9, wait=True):
        #d = buf[:]
        deltat_bins = (np.round(deltat / resolution))
        # print('deltat_bins', deltat_bins)
        if wait:
            start = time.time()
            time.sleep(deltat+0.1)
            last_tag_cputime = 1*self.realtime[0]
            if last_tag_cputime < start:
                return ([0], [0])
            elif last_tag_cputime - start < deltat:
                # print('search for tags')
                deltat = last_tag_cputime - start

        #  pick left and right regions
        right = self.indices[1] - 1
        while not self.valid(right):
            right = right - 1
        left = right - self.size / 2
        if left < 0:
            left = 0
        # print('indices', self.indices, left, right)
        # print('initial left, right timestamp', self[left][1], self[right][1])
        # print('dt', self[right][1]-self[left][1])
        while not self.valid(left):
            left = left + 1
        if (self[right][1] - self[left][1]) < deltat_bins:
                logger.info('requested too mich time')
                idx = left
        else:
            stopbin = self[right][1] - deltat_bins
            idx = self.find_idx(left, right, stopbin)
        # print('indices', self.indices, left, right)
        # print('dt', self[right][1]-self[idx][1])
        # return np.bincount(self[idx:(right)][0])
        histogram = np.unique(self[idx:(right)][0], return_counts=True)
        results = np.zeros(self.channels)
        for (x, n) in zip(histogram[0], histogram[1]):
            if x>0: #  channel numbering starts with 1
                results[x-1] = n
        return results
TTBuffer = Buffer

class CmdBuffer(object):
    def __init__(self):
        self.command = None
        self.fd = None
        self.filename = 'command'
    def query(self):
        # logger.debug('Trying to query command file')
        try:
            fd = shm.read_file(self.filename)
            self.command = fd.readline().strip()
            # logger.debug('command from file: %s' % self.filename)
            fd.close()
            return True
        except ValueError as e:
            # logger.debug('exception in query: %r'%e)
            # logger.debug('filename: %s' % self.filename)
            return False
        except Exception as e:
            logger.info('bad query: %r' % e)
            raise ValueError('Unknown error trying to check if there is a command to run')

    def clear_query(self):
        self.fd = shm.rm(self.filename)

    def write(self, message):
        #  Should add here a check to make sure no command is pending
        self.fd = shm.write_file(self.filename)
        self.fd.write(message)
        self.fd.close()


