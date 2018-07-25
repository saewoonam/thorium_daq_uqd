from __future__ import print_function
#from cffi import FFI
import cffi
import logging


logging.basicConfig(level=logging.WARNING)
logging.getLogger(__name__)

VENDOR_ID = 0x09db
PRODUCT_ID = 0x009c

ffi = cffi.FFI()

# Setup for hidapi calls
ffi.cdef("""
struct hid_device_;
typedef struct hid_device_ hid_device; /**< opaque hidapi structure */


struct hid_device_info {
    char *path;
    unsigned short vendor_id;
    unsigned short product_id;
    wchar_t *serial_number;
    unsigned short release_number;
    wchar_t *manufacturer_string;
    wchar_t *product_string;
    unsigned short usage_page;
    unsigned short usage;
    int interface_number;
    struct hid_device_info *next;
};
int hid_init(void);
int hid_exit(void);
struct hid_device_info* hid_enumerate(unsigned short vendor_id,
                                      unsigned short product_id);
void hid_free_enumeration(struct hid_device_info *devs);
hid_device* hid_open(unsigned short vendor_id, unsigned short product_id,
                     const wchar_t *serial_number);
hid_device* hid_open_path(const char *path);
void hid_close(hid_device *device);
int hid_get_manufacturer_string(hid_device *device, wchar_t *string,
                                size_t maxlen);
int hid_get_product_string(hid_device *device, wchar_t *string,
                           size_t maxlen);
int hid_get_serial_number_string(hid_device *device, wchar_t *string,
                                 size_t maxlen);
""")
logging.info('Try to open libhidapi')
libhidapi = ffi.dlopen( "libhidapi-libusb.so")

#  Setup for libmccusb, specifically usb-USB31XX calls
ffi.cdef("""
void usbDConfigPort_USB31XX(hid_device *hid, uint8_t direction);
void usbDIn_USB31XX(hid_device *hid, uint8_t* din_value);
void usbDOut_USB31XX(hid_device *hid, uint8_t value);
void usbDBitIn_USB31XX(hid_device *hid, uint8_t bit_num, uint8_t* value);
void usbDBitOut_USB31XX(hid_device *hid, uint8_t bit_num, uint8_t value);

void usbAOutConfig_USB31XX(hid_device *hid, uint8_t channel, uint8_t range);
void usbAOut_USB31XX(hid_device *hid, uint8_t channel, uint16_t value, uint8_t update);
void usbAOutSync_USB31XX(hid_device *hid);

void usbInitCounter_USB31XX(hid_device *hid);
uint32_t usbReadCounter_USB31XX(hid_device *hid);

void usbReadMemory_USB31XX( hid_device *hid, uint16_t address, uint8_t count, uint8_t* memory);
int usbWriteMemory_USB31XX(hid_device *hid, uint16_t address, uint8_t count, uint8_t data[]);
void usbBlink_USB31XX(hid_device *hid, uint8_t count);
int usbReset_USB31XX(hid_device *hid);
uint8_t usbGetStatus_USB31XX(hid_device *hid);
void usbPrepareDownload_USB31XX(hid_device *hid);
int usbWriteCode_USB31XX(hid_device *hid, uint32_t address, uint8_t count, uint8_t data[]);
void usbWriteSerial_USB31XX(hid_device *hid, uint8_t serial[8]);
uint16_t volts_USB31XX(uint8_t range, float value);
""")

logging.info('try to open libmccusb')
mcclib = ffi.dlopen("libmccusb.so")

def init():
    logging.debug('Trying to initialize libhadpi in usb3100.py')
    ret = libhidapi.hid_init()
    logging.debug('ret from hid_init %d'%ret)

class dev:
    def __init__(self, PRODUCT_ID=0, name=None, channel=0, range_=1):
        self.meter = None
        logging.debug('Trying to initialize libhadpi in usb3100.py')
        ret = libhidapi.hid_init()
        logging.debug('ret from hid_init %d'%ret)
        self.meter_path = None
        if name is None:
            # use default (hopefully only one) usb31xx device
            # why hopefully only one? by using PRODUCT_ID specification below, we should be able to find a specific one
            VENDOR_ID = 0x09db
            head = libhidapi.hid_enumerate(VENDOR_ID, PRODUCT_ID)
            if head == ffi.NULL:
                raise ValueError('No MCC device found')
            if head.next == ffi.NULL:
                # print('path: ',ffi.string(head.path))
                self.meter_path = ffi.string(head.path)
                # self.meter = libhidapi.hid_open_path(head.path)
                libhidapi.hid_free_enumeration(head)
            else:
                raise ValueError('There are multiple MCC devices')
        else:
            # self.meter = libhidapi.hid_open_path(ffi.new("char[]",name))
            self.meter_path = name
        if self.meter_path is None:
            raise ValueError('Could not open USB device, it is in use already?')
        self.meter = libhidapi.hid_open_path(ffi.new("char[]",
                                                     self.meter_path))
        # print(self.meter_path, self.meter)
        if self.meter == ffi.NULL:
            raise ValueError('Could not open USB device, it is probably already open somewhere')
        self.channel = channel
        self.range_ = range_
        logging.debug('self.meter = %r' % self.meter)
        self.biasDict = {}
        self.close()

    def open_(self):
        logging.debug('open %r' % self.meter_path)
        ret = libhidapi.hid_init()
        if ret != 0:
            raise ValueError('Could not hinit libhidapi, ret: %d' % ret)
            logging.debug('ret from hid_init %d'%ret)
        self.meter = libhidapi.hid_open_path(ffi.new("char[]",self.meter_path))
        # self.meter = libhidapi.hid_open_path(self.meter_path)
        logging.debug('self.meter= %r' % (self.meter))
    def setV(self, value, ch=-1):
        self.open_()
        adc_value = mcclib.volts_USB31XX(self.range_, value)
        if ch==-1:
            ch = self.channel
        #print(self.meter)
        #print(ch)
        #print(adc_value)

        mcclib.usbAOutConfig_USB31XX(self.meter, ch, self.range_)
        mcclib.usbAOut_USB31XX(self.meter, ch, adc_value, 0)
        self.biasDict[ch] = value
        self.close()

    def getV(self, ch=-1):
        if ch==-1:
            ch = self.channel
        return self.biasDict[ch]

    set_volt = setV
    get_volt = getV

    def set_power_on(self):
        pass

    def set_power_off(self):
        self.setV(0, self.channel)

    def blink(self, value):
        self.open_()
        mcclib.usbBlink_USB31XX(self.meter, value)
        self.close()

    #  This code is from https://github.com/jbaiter/hidapi-cffi/blob/master/hidapi.py
    def get_manufacturer_string(self):
        """ Get the Manufacturer String from the HID device.
        :return:    The Manufacturer String
        :rtype:     unicode
        """
        self.open_()
        # self._check_device_status()
        str_p = ffi.new("wchar_t[]", 255)
        rv = libhidapi.hid_get_manufacturer_string(self.meter, str_p, 255)
        if rv == -1:
            raise IOError("Failed to read manufacturer string from HID "
                          "device: {0}".format(self._get_last_error_string()))
        self.close()
        return ffi.string(str_p)

    def get_product_string(self):
        """ Get the Product String from the HID device.
        :return:    The Product String
        :rtype:     unicode
        """
        # self._check_device_status()
        self.open_()
        str_p = ffi.new("wchar_t[]", 255)
        rv = libhidapi.hid_get_product_string(self.meter, str_p, 255)
        if rv == -1:
            raise IOError("Failed to read product string from HID device: {0}"
                          .format(self._get_last_error_string()))
        self.close()
        return ffi.string(str_p)

    def get_serial_number_string(self):
        """ Get the Serial Number String from the HID device.
        :return:    The Serial Number String
        :rtype:     unicode
        """
        # self._check_device_status()
        self.open_()
        str_p = ffi.new("wchar_t[]", 255)
        rv = libhidapi.hid_get_serial_number_string(self.meter, str_p, 255)
        if rv == -1:
            raise IOError("Failed to read serial number string from HID "
                          "device: {0}".format(self._get_last_error_string()))
        self.close()
        return ffi.string(str_p)

    def _check_device_status(self):
        if self.meter is None:
            raise OSError("Trying to perform action on closed device.")

    def identify(self):
        msg = 'Manufacturer: %s\n' % self.get_manufacturer_string()
        msg += 'Product: %s\n' % self.get_product_string()
        msg += 'Serial Number: %s\n' % self.get_serial_number_string()
        msg += 'Channel: %d\n' % self.channel
        return msg

    def close(self):
        logging.debug('Trying to close device')
        libhidapi.hid_close(self.meter)
        self.meter = None
        logging.debug('Trying to exit hidapi')
        ret = libhidapi.hid_exit()
        logging.debug('ret from hid_exit %d'%ret)

if __name__ == '__main__':
    mcc = dev()
    mcc.blink(3)
    print( mcc.identify())
    mcc.setV(1,0)
    mcc.setV(2,1)
    mcc.setV(3,2)
    mcc.setV(4,3)
    # mcc.close()

    # serialID = ffi.new("wchar_t[]",unicode('00105891'))  #  empty string for now, pass Null for one device

    # dev = libhidapi.hid_open(VENDOR_ID, PRODUCT_ID, serialID)
    # dev = libhidapi.hid_open(VENDOR_ID, PRODUCT_ID, ffi.NULL)
    # print (ffi.string(serialID))
    # print (dev)

    # mcclib.usbBlink_USB31XX(dev, 5)
    # logging.info( 'Finished Blinking')
    # range_ = 0  #  0= 0-10V, 1= -10 to 10V
    # adc_value = mcclib.volts_USB31XX(range_,.10)
    # channel = 0
    # mcclib.usbAOutConfig_USB31XX(dev, channel, range_)
    # mcclib.usbAOut_USB31XX(dev, channel, adc_value, 0)
