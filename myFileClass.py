import sys
import sqlite3
import hashlib
import time
import logging
import os.path


logger = logging.getLogger(__name__)
logpath = os.path.dirname(__file__)
logpath = os.path.join(logpath, 'logs/')
fileHandler = logging.FileHandler(logpath + __name__ + '.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.INFO)
logger.addHandler(fileHandler)


def create(fname='hashes.sqlite'):
    conn = sqlite3.connect(fname)
    c = conn.cursor()

    # Create table
    c.execute(
       'CREATE TABLE hashes(filename text, md5 text, sha1 text, hashtime real)'
    )
    conn.commit()

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()


#  based on
#  http://stackoverflow.com/questions/16085292/subclassing-file-objects-to-extend-open-and-close-operations-in-python-3
class _file_obj(object):
    """Check if `f` is a file name and open the file in `mode`.
    A context manager."""
    hashdb = None

    def __init__(self, f, mode):
        if f is None:
            self.file = {
                'r': sys.stdin,
                'a': sys.stdout,
                'w': sys.stdout
            }[mode[0]]
            self.none = True
        elif isinstance(f, str):
            self.file = open(f, mode)
        else:
            self.file = f
        self.close_file = (self.file is not f)
        self.md5 = hashlib.md5()
        self.sha1 = hashlib.sha1()
        # self.hashdb = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if (not self.close_file) or hasattr(self, 'none'):
            return  # do nothing
        # clean up
        exit = getattr(self.file, '__exit__', None)
        if exit is not None:
            return exit(*args, **kwargs)
        else:
            exit = getattr(self.file, 'close', None)
            if exit is not None:
                exit()

    def write(self, rawdata):
        byteswritten = self.file.tell()
        res = self.file.write(rawdata)
        # if res is not None:  # It is None in python2
        #     logger.error('Problem with writing to file, res: %r' % res)
        byteswritten = self.file.tell() - byteswritten
        self.md5.update(rawdata)
        self.sha1.update(rawdata)
        # if self.hashdb is not None:
        #     print('md5: %s, sha1: %s'%(self.md5.hexdigest(),
        #           self.sha1.hexdigest()))
        #     self.updatehashdb()
        return byteswritten

    def close(self):
        if self.hashdb is not None:
            logger.info('md5: %s, sha1: %s' % (self.md5.hexdigest(),
                                               self.sha1.hexdigest()))
            self.updatehashdb()
        return self.file.close()

    def updatehashdb(self):
        conn = sqlite3.connect(self.hashdb)
        c = conn.cursor()
        c.execute("INSERT INTO hashes VALUES (?,?,?,?)",
                  (self.file.name, self.md5.hexdigest(), self.sha1.hexdigest(),
                   time.time()))
        conn.commit()
        conn.close()

    def __getattr__(self, attr):
        return getattr(self.file, attr)

    def __iter__(self):
        return iter(self.file)
