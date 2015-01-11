# -*- coding: utf-8 -*-


"""
    pytelegram
    ~~~~~~~~~
    CFFI-based Telegram bindings for Python based on the tgl C library by
    Vitaly Valtman. See README for details.
    :copyright: Copyright 2014 by Goekcen Eraslan
    :license: LGPL
"""
from cffi import FFI

from . import constants


VERSION = '0.0.1'

#def dlopen(ffi, names):
    #"""Try various names for the same library, for different platforms."""
    #for name in names:
        #try:
            #return ffi.dlopen(name)
        #except OSError:
            #pass
    ## Re-raise the exception.
    #return ffi.dlopen(names[0])

#TGL_LIBS = ['libtgl.so', 'libtgl.0.dylib']

ffi = FFI()
ffi.cdef(constants._TGL_HEADERS, packed=True)
#tgl = dlopen(ffi, TGL_LIBS)

source = '''
#include "tgl.h"
#include "tgl-serialize.h"
#include "tgl-timers.h"
#include "tgl-layout.h"
#include "tgl-binlog.h"
#include "tgl-structures.h"
#include "tgl-eventloop.h"
#include "tgl-net.h"
'''

tgl = ffi.verify(source=source, sources=['tgl/auto/auto.c',
                                         'tgl/binlog.c',
                                         'tgl/mtproto-client.c',
                                         'tgl/mtproto-common.c',
                                         'tgl/queries.c',
                                         'tgl/structures.c',
                                         'tgl/tg-mime-types.c',
                                         'tgl/tgl.c',
                                         'tgl/tgl-serialize.c',
                                         'tgl/tgl-net.c',
                                         'tgl/tgl-timers.c',
                                         'tgl/tgl-eventloop.c',
                                         'tgl/updates.c',
                                         'tgl/tools.c'],
                 include_dirs=['tgl',
                               '/usr/include/event2'],
                 libraries=['event', 'ssl', 'crypto'],
                 ext_package='pytelegram',
                 extra_compile_args=['-ggdb',
                                     '-Wall',
                                     '-Wextra',
                                     #'-Werror',
                                     '-Wno-deprecated-declarations',
                                     '-fno-strict-aliasing',
                                     '-fno-omit-frame-pointer',
                                     '-Wno-unused-parameter'],
                 define_macros=[('EVENT_V2', '1')],
                 undef_macros=['NDEBUG'])

#workaround for CFFI bug:
# https://bitbucket.org/cffi/cffi/commits/932dc0fe2e1644daf91455751654cadb71f14c17
tgl.__dict__.update(constants._MACROS)

