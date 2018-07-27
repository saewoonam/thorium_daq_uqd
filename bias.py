import usb3100
import os
import ruamel.yaml
import time
import struct
import shm_buffer

LOW = 1.3
HIGH = 1.8
buf = shm_buffer.Buffer()
yaml = ruamel.yaml.YAML()
config_file = 'bias.yaml'
vsrc = usb3100.dev(PRODUCT_ID=156)
if os.path.exists(config_file):
    print('Loading')
    bias = yaml.load(open(config_file, 'r'))
else:
    bias = {}
    for i in range(8):
        bias[i] = 0
def save():
    yaml.dump(bias, open(config_file, 'w'))
# print(bias)

def build_ttag(ch, v):
    msg = '%02d %4.3f' % (ch, v)
    out = struct.unpack('Q', msg)[0]
    # print('build_ttag %r' % out)
    return out

def build_ttag_time():
    t = time.time()
    msg = struct.pack('d', t)
    out = struct.unpack('Q', msg)[0]
    return out

def reset(list_=[], high=True):
    global LOW
    print('About to reset')
    buf.add(63, build_ttag_time())
    bias = yaml.load(open(config_file, 'r'))
    if not list_:
        list_ = bias.keys()
    for ch in list_:
        setV(0, ch)
    time.sleep(1)
    for ch in list_:
        if ch==1 and (not high):
            bias[ch] = 1.6
        elif ch==1 and high:
            bias[ch] = 1.6
        if ch==3 and (not high):
            bias[ch] = LOW
        elif ch==3 and high:
            bias[ch] = HIGH
        if ch==3:
            print('high: %r, bias ch4 %f' %(high, bias[ch]))
        setV(bias[ch], ch)
    time.sleep(0.2)


def setV(v, ch):
    print('bias: %.3f, ch: %d' % (v, ch))
    bias[ch] = v
    vsrc.setV(bias[ch], ch)
    buf.add(62, build_ttag(ch, v))
    save()
if __name__ == '__main__':
    reset(high=True)
    # save()

