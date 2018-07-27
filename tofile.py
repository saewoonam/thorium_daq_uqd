import numpy as np
import saveStyle
import time

def continuous(fname, buf, oldpoint):
    while True:
        lastpoint = buf.datapoints
        append(fname, buf[oldpoint:lastpoint])
        oldpoint = lastpoint
        time.sleep(1)

def append(fname, data):
    array = np.zeros(len(data[0]), dtype=saveStyle.DTmin)
    array['ch'] = data[0]
    array['timetag'] = data[1]
    if len(array)>0:
        with open(fname, 'ab') as fp:
            fp.write(array.tobytes())
            fp.flush()
    return array
