import usb31xx
import time
import numpy as np

def reset():
    bias = np.loadtxt('bias.dat')
    vsrc = usb31xx.usb31xx()
    for ch in range(4):
        vsrc.setV(0, ch)
    time.sleep(1)
    for ch in range(4):
        print(bias[ch], ch)
        vsrc.setV(bias[ch], ch)
    vsrc.close()

if __name__ == '__main__':
    reset()
