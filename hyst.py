import usb3100
import os
import ruamel.yaml
import time
import struct
import shm_buffer

buf = shm_buffer.Buffer()
yaml = ruamel.yaml.YAML()
config_file = 'hyst.yaml'
vsrc = usb3100.dev(PRODUCT_ID=158)
if os.path.exists(config_file):
    print('Loading')
    bias = yaml.load(open(config_file, 'r'))
else:
    bias = {}
    for i in range(16):
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

def reset(list_=[]):
    print('About to reset')
    buf.add(59, build_ttag_time())
    bias = yaml.load(open(config_file, 'r'))
    if not list_:
        list_ = bias.keys()
    for ch in list_:
        setV(0, ch)
    time.sleep(1)
    for ch in list_:
        setV(bias[ch], ch)
    time.sleep(0.2)


def setV(v, ch):
    print('bias: %.3f, ch: %d' % (v, ch))
    bias[ch] = v
    vsrc.setV(bias[ch], ch)
    print('try to add event to buf')
    buf.add(60, build_ttag(ch, v))
    save()
if __name__ == '__main__':
    # reset()
    save()

