import os
import sys
import bias
import logzero
import time
from logzero import logger
import struct

import shm_buffer

logzero.logfile('./auto_reset.log')
sys.path.insert(0, '/home/odroid/piServer2')

import client

def build_ttag_time():
    t = time.time()
    msg = struct.pack('d', t)
    out = struct.unpack('Q', msg)[0]
    return out

def get_temp():
    ip = '127.0.0.1'
    port = 50326

    temps = client.client(ip, port, 'getall').split(',')
    return float(temps[1])

if __name__ == '__main__':
    started = True
    temp_rise = 3.1
    temp_fall = 3.1
    #  Try to figure out the state:
    temp = get_temp()
    if temp < temp_fall:
        state = 'cold'
    else:
        state = 'hot'

    while True:
        if state == 'cold':
             while True:
                 temp = get_temp()
                 if temp > temp_rise:
                     logger.info('fridge hot: %.2fK' % temp)
                     state = 'hot'
                     break
                 time.sleep(10)
        else:  # state == hot
            while True:
                temp = get_temp()
                if temp < temp_fall:
                    logger.info('fridge cold: %.2fK' % temp)
                    state = 'cold'
                    logger.info("reset detector")
                    bias.reset()
                    print('reload shm_buffer in case it changed')
                    reload(shm_buffer)
                    buf = shm_buffer.Buffer()
                    buf.add(61,build_ttag_time())
                    print('try to delete buffer to avoid memory leaks')
                    del buf
                    break
                time.sleep(10)

