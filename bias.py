import usb3100
import os
import ruamel.yaml
import time

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


def reset(list_=[]):
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
    save()
if __name__ == '__main__':
    reset()
    # save()

