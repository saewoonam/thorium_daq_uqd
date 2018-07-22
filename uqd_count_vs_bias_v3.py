import time
import datetime
# import usb3100
# import usb31xx
import shm_buffer
import numpy as np
import ruamel.yaml

yaml = ruamel.yaml.YAML()
config={}
with open(__file__[:-3]+'.yaml') as fp:
    config = yaml.load(fp)
offset_dict = config['start_offsets']
integration_time = config['integration_time']
start, stop, step = config['offset_parameters']
# offset_dict = {
#     0: 0,
#     1: 1.3,
#     2: 1,
#     3: 1.3,
# }
# bias = np.zeros(4)
# start, stop, step = 0, 1, 0.01
# integration_time = 1
config['start_offsets'] = offset_dict
config['integration_time'] = integration_time
config['offset_parameters'] = (start, stop, step)
with open(__file__[:-3]+'.yaml','w') as fp:
  config = yaml.dump(config, fp)

buf = shm_buffer.buffer()

def run():
    vsrc = usb31xx.usb31xx()
    vsrc.channel = 1
    for channel in range(4):
        vsrc.set_volt(0, channel)
    directory = '/ssd/'+datetime.datetime.now().strftime('%Y%m%d/')
    if not os.path.exists(directory):
        os.makedirs(directory)
    ttag_directory = directory + basename + '/'
    if not os.path.exists(ttag_directory):
        os.makedirs(ttag_directory)
    basename = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = directory + basename + '.dat'
    filename = 'data/' + filename
    print('filename:', filename)
    fp = open(filename, 'w')
    fp.write('#  integration time: %.2f\n' % integration_time)
    fp.write('# offset_dict: %r\n' % offset_dict)
    fp.write('# offsets: %.2f, %.2f, %.2f\n' % (start, stop, step))
    offset_list = list(np.arange(start, stop, step))
    for offset in offset_list:
        for ch in range(4):
            bias[ch] = offset_dict[ch] + offset
            vsrc.set_volt(bias[ch], ch)
        time.sleep(0.5)
        first_ttag = buf.datapoints
        counts = buf.singles(integration_time)
        last_ttag = buf.datapoints
        tags = buf[first_ttag:last_ttag]
        ttag_filename = ttag_directory + basename + '_%4.3fV' % offset
        tags.tofile(ttag_filename)
        with open(ttag_filename+'.yaml', 'w') as fp:
            config['offset'] = offset
            yaml.dump(config, fp)
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
    run()
