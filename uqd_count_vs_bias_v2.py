import time
import datetime
# import usb3100
import usb31xx
import shm_buffer
import numpy as np

port = '/dev/ttyUSB0'
buf = shm_buffer.buffer()
bkgnd = False
step_size = 0.02
offset_dict = {
    0: 0,
    1: 1.3,
    2: 1,
    3: 1.3,
}
bias = np.zeros(4)

def run():
    vsrc = usb31xx.usb31xx()
    vsrc.channel = 1
    for channel in range(4):
        vsrc.set_volt(0, channel)

    filename = datetime.datetime.now().strftime('%Y%m%d_%H%M%S.dat')
    filename = 'data/' + filename
    print('filename:', filename)
    fp = open(filename, 'w')
    integration_time = 2 
    fp.write('#  integration time: %.2f\n' % integration_time)
    if bkgnd:
        bias_list = [0, 1]
        bias_list.extend(list(np.arange(1.3, 1.8, 0.01)))
    else:
        bias_list = list(np.arange(0, 1, step_size))
    for offset in bias_list:
        for ch in range(4):
            bias[ch] = offset_dict[ch] + offset
            vsrc.set_volt(bias[ch], ch)
        time.sleep(0.5)
        counts = buf.singles(integration_time)
        # print(counts)
        bin_number = counts[0]
        count_in_bin = counts[1]
        counts_histogram = np.zeros(5)
        for bin, counts in zip(bin_number, count_in_bin):
            # print(bin, counts)
            counts_histogram[bin] = counts
        # print(bias, counts_histogram)
        outmsg = ''
        for b, c in zip(bias, counts_histogram[1:]):
            outmsg += '%8.2f %5d'%(b, c)
        print(outmsg)
        fp.write(outmsg+'\n')
        fp.flush()
        # if counts==0 and bias>2.2:
        #     break
    for channel in range(4):
        vsrc.set_volt(0, channel)
    vsrc.close()
#     counter.set_continuous()

if __name__=='__main__':
    while True:
        run()
        raw_input('Hit enter to run again')

