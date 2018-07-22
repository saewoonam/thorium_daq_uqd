# import usb3100
import os
import ruamel.yaml

yaml = ruamel.yaml.YAML()
config_file = 'bias.yaml'

if os.path.exists(config_file):
    bias = yaml.load(open(config_file,'r'))
else:
    bias = {}
    for i in range(8):
        bias[i] = 0
def save():
    yaml.dump(bias, open(config_file,'w'))
# print(bias)
def reset(list_=[]):
    if not list_:
        list_ = bias.keys()
    for ch in list_:
        setV(0, ch)
    for ch in list_:
        setV(bias[ch], ch)

def setV(bias, ch):
    print('bias: %.3f, ch: %d' % (bias, ch))

reset()
save()

