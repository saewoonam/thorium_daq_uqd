from __future__ import print_function
# import uqd
import uqd_fake as uqd
import atexit
import threading
import signal
import numpy as np
import time
import os
import sys
import logging
import logzero
from logzero import logger
from ruamel.yaml import YAML
import shm_buffer
from memory_profiler import profile


logzero.loglevel(logging.INFO)
yaml = YAML()

RUNNING = True
SHOW_PROGRESS = True

def load_settings(number_channels=8):
    global ttag_settings, ttag
    fname = os.path.basename(__file__).split('.py')[0]
    fname = fname + '.yaml'
    if os.path.isfile(fname):
        with open(fname,'r') as f:
            ttag_settings = yaml.load(f)
            logger.debug('ttag settings: %r' % ttag_settings)
            number_channels = len(ttag_settings)
    else:
        logger.debug('use default ttag_settings')
        ttag_settings = []
        for count in range(number_channels):
            ttag_settings.append([0.1+0.1*count, True])
    for channel, setting in enumerate(ttag_settings):
        c = channel + 1  # setting threshold, 1-indexing
        logger.info('setting %d, threshold %f' %(c, setting[0]))
        ttag.set_input_threshold(c, setting[0])
    logger.info('')
    set_mask()
    
    f = shm_buffer.shm.write_file('settings.yaml')
    yaml.dump(ttag_settings, f) 

def save_settings():
    global ttag_settings
    fname = os.path.basename(__file__).split('.py')[0]
    fname = fname + '.yaml'
    with open(fname,'w') as f:
        yaml.dump(ttag_settings, f)

# @atexit.register
def shutdown():
    global RUNNING, cmd, buf, ttag
    RUNNING = False
    print('Trying to shutdown')
    time.sleep(1)
    try:
        ttag.stop()
        ttag.close()
        print('Stopped ttag')
    except Exception as e:
        print('Could not shutdown ttag')
    try:
        shm_buffer.shm.rm('settings.yaml')
        print('Deleted settings from shared memory')
    except Exception as e:
        print('Could not delete cmd')
    try:
        buf.clean()
        del(buf)
        print('Deleted buf')
    except Exception as e:
        print('Could not delete buf')

# signal.signal(signal.SIGINT, shutdown)
# signal.signal(signal.SIGTERM, shutdown)

def build_mask():
    global ttag_settings
    mask = 0
    for idx, item in enumerate(ttag_settings):
        if not item[1]:
            mask = mask + 1 << idx
    return mask 


def set_mask():
    global ttag
    mask = build_mask()
    ttag.set_inversion_mask(mask)
    logger.info('slope mask %s' % (bin(mask)))
    logger.info('')

def main(): 
    global ttag, cmd, buf, RUNNING
    ttag = uqd.CTimeTag()
    ttag.open()
    number_channels = ttag.get_no_inputs()
    print('number of channels %d' % (number_channels))
    load_settings()
    save_settings()
    # sys.exit(-1)
    # buf = ttag_cmd.TTBuffer(0, create=True, datapoints=1<<29)
    # cmd = ttag_cmd.CMDBuffer(0, create=True, ch=number_channels)
    # ch = np.nparray(datapoints=1<<20, dtype=np.uint8) 
    # tags = np.nparray(datapoints=1<<20, dtype=np.uint64) 
    buf = shm_buffer.Buffer(size=1<<24)
    buf.channels = number_channels  # set number of channels available
    cmd = shm_buffer.CmdBuffer()
    logger.debug('Start watch_cmd thread')
    cmd_thread = threading.Thread(target=watch_cmd)
    cmd_thread.start()
    thread = threading.Thread(target=daq)
    thread.start()
    try:
        while RUNNING:
            time.sleep(1)
    except KeyboardInterrupt as e:
        logger.info('Exception: %r' % e)
        RUNNING = False
        shutdown()

def watch_cmd():
    global RUNNING, cmd, buf, ttag, ttag_settings
    logger.info('starting watch command')
    while RUNNING:
        if cmd.query():
            logger.info('got command to process: %s' % cmd.command)
            logger.info('blank line')
            if cmd.command == 'calibrate':
                if ttag.status:
                    logger.info('Can not calibrate while running')
                else:
                    logger.info('starting to calibrate')
                    ttag.calibrate()
                    logger.info('calibrate done')
                # cmd.set_calibrate(False)
                cmd.clear_query()
            elif cmd.command == 'pause':
                ttag.stop()
                cmd.clear_query()
            elif cmd.command == 'unpause':
                ttag.start()
                cmd.clear_query()
            elif cmd.command == 'trigger':
                if ttag.status:
                    ttag.stop()
                f = shm_buffer.shm.read_file('settings.yaml')
                new_settings = yaml.load(f)
                send_mask_bool = False
                for i in range(len(new_settings)):
                    if new_settings[i] != ttag_settings[i]:
                        if new_settings[i][0] != ttag_settings[i][0]:
                            #  Change threshold
                            ch = i+1
                            level = new_settings[i][0]
                            ttag.set_input_threshold(ch, level)
                            buf.add(29, ch)
                            logger.info('changed ch %d threshold to %f' % (ch, level))
                        if new_settings[i][1] != ttag_settings[i][1]:
                            send_mask_bool = True
                ttag_settings = new_settings
                if send_mask_bool:
                    set_mask();
                    buf.add(29, 64)
                cmd.clear_query()
                save_settings()
                ttag.start()
                logger.info('')  # add extra line to so messages are not overwritten
            else:
                logger.error('Unknown command: %s' % cmd.command)
                logger.error('blank line')
                cmd.clear_query()
        time.sleep(1)


@profile
def daq_test():
    # ttag, buf, cmd = configuration
    global ttag, cmd, buf, RUNNING
    print('Running')
    ttag.start()
    while RUNNING:
        error_ = ttag.read_error_flags()
        if error_:
            buf.add(30, error_)
            logger.info(ttag.get_error_text(error_))
        result = ttag.read()
        if SHOW_PROGRESS:
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            print(len(result[0]))
        del(result)
        time.sleep(0.1)

# @profile
def daq():
    # ttag, buf, cmd = configuration
    overwrite = True  # overwrite line when updating
    global ttag, cmd, buf, RUNNING
    print('')
    ttag.start()
    print('started')
    while RUNNING:
        error_ = ttag.read_error_flags()
        if error_:
            buf.add(30, error_)
            print(error_, ttag.get_error_text(error_))
            logger.info(ttag.get_error_text(error_))
        if ttag.status:
            result = ttag.read()
            if result is not None:
                if len(result[0])==0:
                    # logger.info('reassign result to None')
                    # logger.info('')
                    result = None
        else:
            result = None
        # logger.debug('error, Result, %d, %r' % (error, type(result)))
        if result is not None:
        # if False:
            channels = result[0]
            tags = result[1]
            #  channels and tags are bytearrays from ttag.ReadTags
            if len(channels) != len(tags):
                logger.debug('Serious error, channels and tags length mismatch')
            else:
                buf.addarray(channels, tags)
                if SHOW_PROGRESS:
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                    print(time.asctime(), '(num, index_to_write)',
                          (len(channels), buf.indices[1]))
                    overwrite = False
                # del(channels)
                # del(tags)
                # del(result)
        else:
            time.sleep(0.25)
            # if overwrite:
            #     sys.stdout.write("\033[F")
            #     sys.stdout.write("\033[K")
            #     overwrite = True
            # print(time.asctime())


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        RUNNING = False
        logger.info('%r' % e)
        shutdown()

