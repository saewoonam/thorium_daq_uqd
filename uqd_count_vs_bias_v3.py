import os
import time
import datetime
import usb3100
# import usb31xx
import shm_buffer
import numpy as np
import ruamel.yaml

yaml = ruamel.yaml.YAML()
config={}
with open(__file__[:-3]+'.yaml') as fp:
    print('loading')
    config = yaml.load(fp)
offset_dict = config['start_offsets']
integration_time = config['integration_time']
start, stop, step = config['offset_parameters']
print(config)
# offset_dict = {
#     0: 0,
#     1: 1.3,
#     2: 1,
#     3: 1.3,
# }
# bias = np.zeros(4)
# start, stop, step = 0, 1, 0.01
# integration_time = 1
# config['start_offsets'] = offset_dict
# config['integration_time'] = integration_time
# config['offset_parameters'] = (start, stop, step)
with open(__file__[:-3]+'.yaml','w') as fp:
    yaml.dump(config, fp)

buf = shm_buffer.Buffer()

def run():
    global config
    vsrc = usb3100.dev()
    vsrc.channel = 1
    for channel in range(4):
        vsrc.set_volt(0, channel)
    basename = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    directory = '/ssd/'+datetime.datetime.now().strftime('%Y%m%d/')
    if not os.path.exists(directory):
        os.makedirs(directory)
    ttag_directory = directory + basename + '/'
    if not os.path.exists(ttag_directory):
        os.makedirs(ttag_directory)
    filename = directory + basename + '.dat'
    # filename = 'data/' + filename
    print('filename:', filename)
    fp_data = open(filename, 'w')
    fp_data.write('#  integration time: %.2f\n' % integration_time)
    fp_data.write('# offset_dict: %r\n' % offset_dict)
    fp_data.write('# offsets: %.2f, %.2f, %.2f\n' % (start, stop, step))
    offset_list = list(np.arange(start, stop, step))
    bias = np.zeros(4)
    for offset in offset_list:
        for ch in range(4):
            bias[ch] = float(offset_dict[ch] + offset)
            vsrc.set_volt(bias[ch], ch)
        time.sleep(0.5)
        first_ttag = buf.datapoints
        counts = buf.singles(integration_time)
        last_ttag = buf.datapoints
        # print(first_ttag, last_ttag)
        if last_ttag > first_ttag:
            tags = buf[first_ttag:last_ttag]
        else:
            tags = ()
        tags = np.array(tags)
        ttag_filename = ttag_directory + basename + '_%4.3fV' % offset
        tags.tofile(ttag_filename)
        with open(ttag_filename+'.yaml', 'w') as fp:
            for i in range(4):
                bias[i] = float(bias[i])
            config['bias'] = 'need to fix'
            yaml.dump(config, fp)
        # print(counts)
        outmsg = ''
        counts = counts[:4]
        for b, c in zip(bias, counts):
            outmsg += '%8.2f %5d'%(b, c)
        print(outmsg)
        fp_data.write(outmsg+'\n')
        fp_data.flush()
        # if counts==0 and bias>2.2:
        #     break
    for channel in range(4):
        vsrc.set_volt(0, channel)
    # vsrc.close()
#     counter.set_continuous()

if __name__=='__main__':
    run()
