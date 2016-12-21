'''
Parser for JSON streams capable of starting at an arbitrary location and
"figuring it out."
'''

from ._jsua import lib, ffi
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from enum import Enum
from six import with_metaclass, print_
import traceback
import sys

class EventType(Enum):
    OBJ_START   = lib.JSUA_EVT_OBJ_START
    OBJ_END     = lib.JSUA_EVT_OBJ_END
    ARR_START   = lib.JSUA_EVT_ARR_START
    ARR_END     = lib.JSUA_EVT_ARR_END
    VAL_STR     = lib.JSUA_EVT_VAL_STR
    VAL_NUM     = lib.JSUA_EVT_VAL_NUM
    VAL_BOOL    = lib.JSUA_EVT_VAL_BOOL
    VAL_NULL    = lib.JSUA_EVT_VAL_NULL
    COLON       = lib.JSUA_EVT_COLON
    COMMA       = lib.JSUA_EVT_COMMA

EVENT_TYPES = sorted((
    EventType.OBJ_START,
    EventType.OBJ_END,
    EventType.ARR_START,
    EventType.ARR_END,
    EventType.VAL_STR,
    EventType.VAL_NUM,
    EventType.VAL_BOOL,
    EventType.VAL_NULL,
    EventType.COLON,
    EventType.COMMA,
), key=lambda x: x.value)

Event = namedtuple('Event', ['type', 'completed', 'data'])

class ParseError(ValueError):
    pass

class Parser(with_metaclass(ABCMeta)):
    def __init__(self):
        self._handle = ffi.new_handle(self)
        self._ptr = lib.jsua_parser_new()
        if self._ptr == ffi.NULL:
            raise MemoryError
        if not lib.jsua_parser_init(self._ptr,
                                    lib.on_parser_event,
                                    self._handle):
            lib.jsua_parser_free(self._ptr)
            self._ptr = ffi.NULL
            raise MemoryError

    def __del__(self):
        lib.jsua_parser_fini(self._ptr)
        lib.jsua_parser_free(self._ptr)
        self._ptr = ffi.NULL

    def feed(self, blob):
        ptr = blob._ptr
        blob.release()
        if not lib.jsua_parser_feed(self._ptr, ptr):
            error = lib.jsua_parser_error(self._ptr)
            error_type = ffi.string(lib.jsua_error_to_string(error))
            error_type = error_type.decode('utf-8')
            raise ParseError('{} near: {} (char {})'.format(
                             error_type,
                             ffi.unpack(ffi.cast('char*', error.sample),
                                        error.sample_size),
                             error.error_offset))

    @abstractmethod
    def on_event(self, event):
        pass

def _on_event_error(exc, exc_value, tb):
    import os
    print_('Exception in JSUA parser callback:', file=sys.stderr)
    traceback.print_exception(exc, exc_value, tb, file=sys.stderr)
    os._exit(1)

@ffi.def_extern(onerror=_on_event_error)
def on_parser_event(event, user_data):
    parser = ffi.from_handle(user_data)
    data = None
    if event.size and ffi.NULL != event.data:
        data = ffi.unpack(ffi.cast('char*', event.data), event.size)
    parser.on_event(Event(type=EVENT_TYPES[event.type],
                          completed=bool(event.completed),
                          data=data))
