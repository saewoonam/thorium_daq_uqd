import os
import zmq
import time
import datetime
import logging
import logzero
from logzero import logger

logzero.loglevel(logging.INFO)
class Lock:
    def __init__(self, name = 'lock_name'):

        port = 5556
        context = zmq.Context()
        logger.debug("Connecting to server...")
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:%s" % port)
        self.socket = socket
        self.name = name
        self.pid = os.getpid()
        self._create()

    def _create(self):
        socket = self.socket
        socket.send_string('create %s' % self.name)
        msg = socket.recv()
        #  Should check msg
        logger.debug('msg from init/create %r' % msg)

    def acquire(self):
        socket = self.socket
        while True:
            self.id = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S_")
            self.id += '%d' % self.pid
            socket.send_string('lock %s %s' % (self.id, self.name))
            msg = socket.recv()
            logger.debug('msg from acquire: %r' % msg)
            if msg.startswith(b'locked'):
                break
            if msg.startswith(b'unrecognized'):
                #  Something happened to the server, it must have restarted, so
                #  we must re-create the lock
                self._create()
            #  Need to keep trying to get the lock

    def release(self):
        socket = self.socket
        socket.send_string('unlock %s %s' % (self.id, self.name))
        msg = socket.recv()
        logger.debug('msg from release: %r' % msg)

    def _status(self):
        self.socket.send_string('status')
        return self.socket.recv()

    def __enter__(self):
        self.acquire()

    def __exit__(self, *args):
        self.release()
        logger.debug('exit args:')
        logger.debug(args)

if __name__ == '__main__':
    lock = Lock('test')
    lock.acquire()
    time.sleep(10)
    lock.release()
