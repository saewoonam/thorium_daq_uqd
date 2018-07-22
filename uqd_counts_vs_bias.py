import numpy as np
import time
import datetime
# import usb3100
import usb31xx
import shm_buffer

port = '/dev/ttyUSB0'
buf = shm_buffer.buffer()
bkgnd = False
step_size = 0.02
offset_dict = {
    0: 0.3,
    1: 1.7,
    2: 1.3,
    3: 1.7,
}
def run():
    vsrc = usb31xx.usb31xx()
    vsrc.channel = 1
    for channel in range(4):
        vsrc.set_volt(0, channel)

    filename = datetime.datetime.now().strftime('%Y%m%d_%H%M%S.dat')
    filename = 'data/' + filename
    print('filename:', filename)
    fp = open(filename, 'w')
    if bkgnd:
        bias_list = [0, 1]
        bias_list.extend(list(np.arange(1.3, 1.8, 0.01)))
    else:
        bias_list = [0, 0.5]
        bias_list.extend(list(np.arange(1.3, 2.2, step_size)))
    for bias in bias_list:
        for ch in range(4):
            vsrc.set_volt(bias, ch)
        time.sleep(0.5)
        counts = buf.singles(1)
        outmsg = '%5.2f %r' % (bias, counts)
        print(outmsg)
        fp.write(outmsg+'\n')
        # if counts==0 and bias>2.2:
        #     break
    vsrc = usb31xx.usb31xx()
    vsrc.channel = 1
    for channel in range(4):
        vsrc.set_volt(0, channel)
    vsrc.close()
#     counter.set_continuous()

if __name__=='__main__':
    while True:
        run()
        raw_input('Hit enter to run again')

