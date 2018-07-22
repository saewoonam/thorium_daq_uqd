#!/usr/bin/env python
'''
@author: qittlab

Server to monitor a ttag remotely.

'''

import time
import threading
import yaml
import argparse
# import atexit
from multiprocessing import Process, Value
import zmq
import logging
import os
import numpy as np
import UQDLogger
import json
import Spinner


#  Set up logging to file and level to console
logger = logging.getLogger('bell_server2')
logpath = os.path.dirname(__file__)
logpath = os.path.join(logpath, 'logs/')
fileHandler = logging.FileHandler(logpath + 'bell_server2.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.INFO)
logger.addHandler(fileHandler)
logging.basicConfig(level=logging.INFO)

#  Load config from yaml file
config_fp = open('bell_server.yaml', 'r')
config = yaml.load(config_fp)
config_fp.close()
bufferNumber = config['buffer']
#  Get commandline args
parser = argparse.ArgumentParser()
parser.add_argument(
    "-b", type=int, default=bufferNumber, help='memory buffer number')
args = parser.parse_args()


class Daq():
    """  Simple wrapper class to make sure the logging is done in a
    different process
    """

    def __init__(self):
        self.running = False
        self.dataloggerRunning = Value('b', False)
        self.datalogger = UQDLogger.UQDLogger(
            args.b, self.dataloggerRunning, usegps=config['usegps'])
        self.logLock = threading.Lock()
        logger.info("finished daq init, logging wrapper")

    def start(self, fnameStr='', sec=-1):
        if not self.running:
            self.running = True
            self.daq_thread = threading.Thread(None, self.run, args=[fnameStr])
            self.daq_thread.start()
        else:
            logger.info('DAQ is already running')

    def stop(self):
        self.running = False
        if hasattr(self, 'datalogger'):
            with self.logLock:
                self.datalogger.stop()

    def run(self, fnameStr):
        with self.logLock:
            self.datalogger.init(
                folder=config['destfolder'], subfolder='bell', suffix=fnameStr)
            Process(target=self.datalogger.start).start()
            logger.info("started logging process")


daq = Daq()


def handle(cmd):
    cmd = cmd.decode('UTF-8')
    cmd = cmd.split()
    logger.debug(cmd)
    if cmd[0].lower() == 'done':
        # stop daq thread
        # self.daq.stop()
        response = b'done'
    elif cmd[0].lower() == 'logging' or cmd[0].lower() == 'log':
        logger.info('logging: %r' % cmd)
        # start daq thread
        if len(cmd) > 1:
            # Parse commands to determine if logging on or off
            if cmd[1].lower() == 'off':
                logger.info('trying to stop logging')
                daq.stop()
            else:  # turn on
                if len(cmd) == 2:
                    daq.start()
                else:
                    daq.start(cmd[2])
                # wait until running before continue
                while not daq.dataloggerRunning.value:
                    time.sleep(0.001)
        else:  # if no 'on' or 'off' string then turn on
            daq.start()
            # wait until running before continue
            while not daq.dataloggerRunning.value:
                time.sleep(0.001)
        logger.info('log, filename: %s' % daq.datalogger.filename)
        response = daq.datalogger.filename.encode('UTF-8')
    elif cmd[0].lower() == 'start':  # start time tagger (not log)
        logging.info('Starting: %r' % cmd)
        daq.datalogger.startbuff()
        response = b'started'
    elif cmd[0].lower() == 'stopbuff' or cmd[0].lower() == 'stop':  # stop ttag
        logging.info('Stopping buf')
        # stop daq thread
        daq.datalogger.stopbuff()
        response = b'stopped'
    elif cmd[0].lower() == 'stream':
        if len(cmd) > 1:
            dt = float(cmd[1])
        else:
            dt = 0.1
        raw = daq.datalogger.buff(dt)  # retrieve raw data directl
        try:
            data = np.array(raw)
            data = data.T
        except:
            logging.error("Error in streaming, buffer to small?")
            logging.error("raw: %r" % raw)
            data = np.empty((10, 2))
            data.fill(-1)
        response = data.tobytes()
        # response = compress_data(raw)
    elif cmd[0].lower() == 'getcounts':
        if len(cmd) > 1:
            dt = float(cmd[1])
        else:
            dt = 1

        counts = daq.datalogger.buff.singles(dt)
        response = json.dumps(counts.tolist()).encode('UTF-8')
    else:
        response = b"Command not recognized"
    logging.debug('response type: %r' % type(response))
    return response


def cleanup():
    logger.info("Cleaning up...")
    if daq.running:
        logger.info("stop logging")
        daq.stop()
    daq.datalogger.buff.stop()


if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    try:
        socket.bind('tcp://*:%d' % config['port'])
        print('Connected to port: %d' % config['port'])
    except:
        logger.error('Could not connect to port %d' % config['port'])
        logger.error('try port 5555')
        socket.bind('tcp://*:5555')
        print('Connected to port: 5555')
    while True:
        try:
            spinner = Spinner.Spinner()
            spinner.start()
            message = socket.recv()
            spinner.stop()
        except KeyboardInterrupt:
            print('Keyboard interrupt, trying to shutdown')
            spinner.stop()
            break
        response = handle(message)
        socket.send(response)
    # Need to cleanup
    cleanup()
    socket.close()
    context.term()
