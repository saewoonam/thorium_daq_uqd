import zmq
import time
import sys
import psutil
import threading
import logging
import logzero
from logzero import logger


logzero.loglevel(logging.INFO)
port = "5556"
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % port)

LOCKS = {'default': [False, 0]}

def process_lock(key, message_id):
    global LOCKS
    if key not in LOCKS:
        response = 'unrecognized lock: %s' % key
        return response
    locked, pid = LOCKS[key]
    if locked:
        response = 'Already locked by another process %d' % pid
    else:
        locked = True
        # pid = int(pid_message)
        LOCKS[key] = [locked, message_id]
        print('locked by: %r' % message_id)
        response = 'locked by %r' % message_id
    return response

def process_unlock(key, message_id=''):
    global LOCKS
    if key not in LOCKS:
        response = 'unrecognized unlock: %s' % key
        return response
    else:
        if LOCKS[key][1] == message_id:
            LOCKS[key] = [False, 0]
            response = 'unlocked %s' % key
        else:
            response = 'failed to unlock; mismatched id: %r %r' % \
                    (LOCKS[key][1], message_id)

    return response

def check_pid():
    logger.debug('Check_pids')
    for key in LOCKS:
        if LOCKS[key][0]:
            lock_id = LOCKS[key][1]
            pid = int(lock_id.decode().split('_')[-1])
            logger.debug('check pid: %d' % pid)
            if not psutil.pid_exists(pid):
                logger.debug('lock_id %s, pid does not exist, removing' % lock_id)
                LOCKS[key] = [False, 0]
    time.sleep(1)
    check_thread = threading.Thread(target=check_pid)
    if socket is not None:
        check_thread.start()

check_pid()
while True:
    #  Wait for next request from client
    try:
        message = socket.recv()
    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")
        break;
    # print("Received request: %r" % message)
    # time.sleep (10)
    message = message.split()
    request = message[0].decode().lower()
    print(message)
    print(request)
    if request == 'lock':
        if len(message) == 2:
            response = process_lock('default', message[1])
        elif len(message) == 3:
            response = process_lock(message[2], message[1])
    elif request == 'unlock':
        if len(message) == 1:
            response = process_unlock('default')
        elif len(message) == 3:
            response = process_unlock(message[2], message[1])
    elif request == 'create':
        if len(message) == 2:
            key = message[1]
            if key not in LOCKS:
                LOCKS[key] = [False, 0]
                response = 'Created lock: %r' % key
            else:
                response = 'Already exists: %r' % key
        else:
            response = 'Failed to create a lock'
    elif request == 'status':
        response = '%r' % LOCKS
    else:
        response = 'failed to understand: %s' % request

    socket.send_string(response)

# clean up
socket.close()
context.term()
socket = None
