from cffi import FFI
import os
import mmap
import numpy
import struct
import platform
import logging
import logzero
from logzero import logger


if os.name == 'nt':
    uname = 'nt'
else:
    uname = platform.os.uname()
    posix()
logzero.loglevel(logging.INFO)
def posix():
    global ffi, C, uname
    # logzero.loglevel(logging.DEBUG)
    ffi = FFI()
    if uname[0]=='Darwin':
        ffi.cdef("""
            //  osx typdefs
            typedef uint16_t  mode_t;
            typedef int64_t   off_t;
            //
        """)
    elif uname[0]=='Linux':
        logger.debug('Linux')
        ffi.cdef("""
            // /usr/include/arm-linux-gnueabihf/bits/types.h
            // typedef __U32_TYPE  mode_t;
            typedef unsigned int  mode_t;
            // typedef __SLONGWORD_TYPE   off_t;
            typedef long int   off_t;
            //
        """)
    ffi.cdef("""
        int printf(const char *format, ...);   // copy-pasted from the man page
        int shm_open(const char *name, int oflag, mode_t mode);
        int shm_unlink(const char *name);
        int ftruncate(int fd, off_t length);
        void *memset(void *s, int c, size_t n);
        void *mmap(void *addr, size_t length, int prot, int flags,
                      int fd, off_t offset);
        int munmap(void *addr, size_t length);
    """)
    if uname[0]=='Darwin':
        C = ffi.dlopen(None)
    else:
        C = ffi.dlopen('librt.so')

    # arg = ffi.new("char[]", b"Hello")
    # C.printf(b"World %s\n", arg)

def new(name, shape, dt=numpy.double):
    global ffi, C
    dt = numpy.dtype(dt)
    footer = create_footer(shape, dt)
    size = numpy.prod(shape) * dt.itemsize  # size in bytes

    if uname != 'nt':
        arg = ffi.new("char[]", b"/"+name.encode())
        mode = ffi.cast("mode_t", 0o666)
        fd = C.shm_open(arg, os.O_RDWR | os.O_CREAT | os.O_EXCL, mode)
        if fd < 0:
            raise ValueError("Can't open shared memory:%s, %d Error %s" % \
                            (name, ffi.errno, os.strerror(ffi.errno)))
        logger.debug('fd = %d' % (fd))
        result = C.ftruncate(fd, size+len(footer));
        logger.debug('fruncate result: %d' % result)
        if result < 0:
            raise ValueError("Can't allocate memory for %s, %d Error %s" % \
                            (name, ffi.errno, os.strerror(ffi.errno)))

        # get size from os, on osx/Darwin, the size is a multiple of 4096
        # size = os.fstat(fd).st_size

        logger.debug('mmap size: %d' %(os.fstat(fd).st_size))
        map_ = mmap.mmap(fd, os.fstat(fd).st_size)
    else:
        #  Much simpler in Windows
        map_ = mmap.mmap(0, size, name)
    map_[-len(footer):] = footer
    # map_.close()
    return numpy.ndarray(shape=shape, buffer=map_, dtype=dt)

def connect(name):
    global ffi, C
    if uname != 'nt':
        arg = ffi.new("char[]", b"/"+name.encode())
        # arg = ffi.new("char[]", b"/test")
        mode = ffi.cast("mode_t", 0o666)
        fd = C.shm_open(arg, os.O_RDWR | os.O_EXCL, mode)
        if fd < 0:
            raise ValueError("Can't open shared memory:%s, %d Error %s" % \
                            (name, ffi.errno, os.strerror(ffi.errno)))
        logger.debug('fd = %d' % (fd))

        # print('size:', os.fstat(fd).st_size)
        map_ = mmap.mmap(fd, os.fstat(fd).st_size)
        # print(map_)
    else:
        map_ = mmap.mmap(0, size, name)
    fmt = '16sBBi'+numpy.MAXDIMS*'i'
    footer_struct = struct.Struct(fmt)
    footer = map_[-footer_struct.size:]
    # print(footer)
    footer = struct.unpack(fmt, footer)
    magic = footer[0]
    dtnum = footer[1]
    ndims = footer[2]
    size = footer[3]
    shape = footer[4:(4+ndims)]
    # print(magic, dtnum, ndims, size, shape)
    if magic == 'saewoo_magic_str':
        dt = numpy.sctypeDict[dtnum]
        return numpy.ndarray(shape=shape, buffer=map_, dtype=dt)
    else:
        raise ValueError('%s, header is not understood' % (name))

def create_footer(shape, dt=numpy.double):
    #  fmt:
    #  16s: 'saewoo_magic_str'
    #  byte: dtype
    #  byte: ndims
    #  i:  size
    #  32*i: dims array
    fmt = '16sBBi'+numpy.MAXDIMS*'i'
    magic = b'saewoo_magic_str'
    if type(shape) is tuple:
        args = (fmt, magic, dt.num, len(shape), numpy.prod(shape), ) + \
               shape + (0,)*(numpy.MAXDIMS-len(shape))
        footer = struct.pack(*args)
        # footer = struct.pack(fmt, magic, dt.num, len(shape),
        #                      numpy.prod(shape),
        #                      *shape, (0,)*(numpy.MAXDIMS-len(shape)))
    else:
        args = (fmt, magic, dt.num, 1, shape, shape,) + \
                             (0,)*(numpy.MAXDIMS-1)
        # print(args)
        footer = struct.pack(*args)
        # footer = struct.pack(fmt, magic, dt.num, 1, shape, shape,
        #                      (0,)*(numpy.MAXDIMS-1))
    return footer

def rm(name):
    global ffi, C
    if uname != 'nt':
        arg = ffi.new("char[]", b"/"+name.encode())
        result = C.shm_unlink(arg);
        if result < 0:
            raise ValueError('Could not remove %s, %d Error %s' % \
                            (name, ffi.errno, os.strerror(ffi.errno)))

        logger.debug(result)

def write_file(name):
    global ffi, C
    try:
        rm(name)
    except:
        pass
    arg = ffi.new("char[]", b"/"+name.encode())
    mode = ffi.cast("mode_t", 0o666)
    fd = C.shm_open(arg, os.O_RDWR | os.O_CREAT | os.O_EXCL, mode)
    if fd < 0:
        raise ValueError("Can't open shared memory:%s, %d Error %s" % \
                        (name, ffi.errno, os.strerror(ffi.errno)))
    logger.debug('fd = %d' % (fd))
    return os.fdopen(fd, "w") 

def read_file(name):
    global ffi, C
    arg = ffi.new("char[]", b"/"+name.encode())
    # arg = ffi.new("char[]", b"/test")
    mode = ffi.cast("mode_t", 0o666)
    fd = C.shm_open(arg, os.O_RDWR | os.O_EXCL, mode)
    if fd < 0:
        raise ValueError("Can't open shared memory:%s, %d Error %s" % \
                        (name, ffi.errno, os.strerror(ffi.errno)))
    logger.debug('fd = %d' % (fd))
    return os.fdopen(fd, "r")

def clear_mem():
    global ffi, C
    #  This is something that I cut out of the linux code...
    #   Not needed because of a programming error
    #  Clear memory, on linux it seems to be not zero'ed out
    ptr = ffi.new('unsigned char *ptr')
    # ptr = ffi.new_handle()
    ptr = C.mmap(ffi.NULL, size, mmap.PROT_READ | mmap.PROT_WRITE,
                 mmap. MAP_SHARED,
                 fd, 0);
    print(ptr)
    print(ffi.cast('unsigned char *', ptr)[0])
    C.memset(ptr, 0, size)
    for loop in range(size):
        print(loop, ffi.cast('unsigned char *', ptr)[loop])
    result = C.munmap(ptr, size) 
    logger.debug('result of unmap %d' % (result))

