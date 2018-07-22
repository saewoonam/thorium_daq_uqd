import os
# import ttag_cmd as ttag
import shm_buffer as ttag
import numpy as np
import datetime
import saveStyle
import logging
import myFileClass
import socket
import functools

hostname = socket.gethostname()
logger = logging.getLogger(__name__)
logpath = os.path.dirname(__file__)
logpath = os.path.join(logpath, 'logs/')
fileHandler = logging.FileHandler(logpath + __name__ + '.log')
fileHandler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

myFileClass._file_obj.hashdb = logpath + 'hashes.db'


class UQDLogger(object):
    def __init__(self, num=-1, running=False, usegps=True):
        if num == -1:  # if no buffer number is specified
            num = ttag.getfreebuffer()
            logger.info("next free buffer: %d" % num)
        else:
            num = num + 1
        buf = ttag.TTBuffer(num - 1)
        # buf = shm_buffer.buffer(num - 1)
        # cmd = ttag.CMDBuffer(num - 1)

        if ttag.__name__ == 'shm_buffer':
            self.cmd = ttag.CmdBuffer()
            self.buff.start = functools.partial(self.cmd.write, 'unpause')
            self.buff.stop = functools.partial(self.cmd.write, 'pause')

        self.fname = ''
        self.buff = buf
        self.buff.tagsAsTime = False
        self.filename = ''
        self.buffStarted = False
        self.running = running

    def init(self, folder='', subfolder='', prefix='', suffix=''):
        self.filename = self.createfilename(
            folder=folder, subfolder=subfolder, prefix=prefix, suffix=suffix)
        logger.info('Trying to open: %s' % self.filename)
        # self.f = open(self.filename,'wb')
        # os.chmod(self.filename,0666)
        # self.f = os.fdopen(os.open(self.filename,
        #                            os.O_WRONLY|os.O_CREAT, 0666), 'wb')
        oldmask = os.umask(0o022)
        self.f = myFileClass._file_obj(self.filename, 'wb')
        hashpath = os.path.abspath(
            os.path.join(os.path.dirname(self.filename), '..'))
        hashpath = os.path.join(hashpath, 'hashes.db')
        if not os.path.exists(hashpath):
            myFileClass.create(hashpath)
        self.f.hashdb = hashpath
        os.chmod(self.filename, 0o0644)
        newmask = os.umask(oldmask)
        if not self.buffStarted:
            self.startbuff()
        self.sleeptime = 1
        # time.sleep(1)

    def start(self):
        logger.info('Starting logging')
        # print self.running
        self.running.value = True
        # print "set running value"
        self.run()

    @staticmethod
    def compress_data(data, xferCount=0):
        data_to_store = np.zeros(data.shape[1], dtype=saveStyle.DT)
        data_to_store['ch'] = data[0, :].astype('u1')
        data_to_store['timetag'] = data[1, :]
        data_to_store['xfer'] = np.ones(data.shape[1]).astype('u2') * xferCount
        return data_to_store

    def run(self):
        oldend = self.buff.datapoints
        logger.info('datapoints start: %d' % oldend)
        xferCount = 0
        if oldend > 0:
            lasttag = self.buff[oldend - 1][1]
        else:
            lasttag = 0

        while self.running.value:
            end = self.buff.datapoints
            if end > oldend:
                data = self.buff[oldend:end]
                data = np.array(data)
                #  create memory to save data in more compact format
                data_to_store = self.compress_data(data, xferCount)
                try:
                    byteswritten = self.f.tell()
                    self.f.write(data_to_store.tostring())
                    # self.f.flush()
                    byteswritten = self.f.tell() - byteswritten
                except Exception as e:
                    #  Should have more extensive information logged here...
                    msg = "Problem writing to file, trying again: %r" % e
                    logger.info(msg)
                    # byteswritten = self.f.write(data_to_store.tobytes())
                    byteswritten = self.f.write(data_to_store.tostring())
                    # data_to_store.tofile(self.f)
                if byteswritten != saveStyle.DT.itemsize * len(data_to_store):
                    logger.error(
                        'Problem logging bytes written: %r, expected %r, %r' %
                        (byteswritten,
                         saveStyle.DT.itemsize * len(data_to_store),
                         len(data_to_store.tostring())))
                self.f.flush()
                firsttag = data[1, 0]  # row 1 (2nd row), first entry/column
                if firsttag < lasttag:
                    logger.error('problem with xfer %d %d, %d' %
                                 (lasttag, firsttag, lasttag - firsttag))
                    logger.error('%d  %d  %d' % (xferCount, oldend, end))

                lasttag = data[1, -1]  # row 1, last entry
                oldend = end
                xferCount += 1
            # else:
            # print 'No data from ttag'

            # time.sleep(self.sleeptime)
        logger.info('stop logging')
        self.f.close()

    def stop(self):
        self.running.value = False
        # self.buff.stop()

    def stopbuff(self):
        self.buff.stop()
        self.buffStarted = False

    def startbuff(self):
        self.buff.start()
        self.buffStarted = True

    @staticmethod
    def createfilename(folder='', subfolder='', prefix='', suffix=''):
        d = datetime.datetime.now()  # current date and time for filename
        destfolder = folder
        if len(destfolder) == 0:
            destfolder = './'
        if not destfolder.endswith('/'):
            destfolder += '/'
        logger.info('destfolder:%s' % destfolder)
        if len(subfolder) == 0:
            localdatafolder = destfolder + '%s/' % (
                hostname) + d.strftime('%Y_%m_%d')
        else:
            localdatafolder = destfolder + '%s/%s/' % (
                subfolder, hostname) + d.strftime('%Y_%m_%d')
        localdatafolder = os.path.expanduser(
            localdatafolder)  # expand ~ in OS dependent way
        logger.info('localdatafolder: %s' % localdatafolder)
        if not os.path.isdir(
                localdatafolder):  # make the file folder if it doesn't exist
            logger.info('Creating: %s' % (localdatafolder))
            try:
                oldmask = os.umask(0o022)
                os.makedirs(localdatafolder, 0o0777)
            finally:
                newmask = os.umask(oldmask)
        if len(suffix) > 0:
            if not suffix.startswith('_'):
                suffix = '_' + suffix
        fileName = localdatafolder + '/' + prefix + d.strftime(
            '%Y_%m_%d_%H_%M') + suffix + '.dat'
        return fileName
