'''
Parser for JSON streams capable of starting at an arbitrary location and
"figuring it out."
'''

from ._jsua import lib, ffi
from abc import ABCMeta, abstractmethod

class ParseError(ValueError):
    pass

class Parser(metaclass=ABCMeta):
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

@ffi.def_extern()
def on_parser_event(event, user_data):
    parser = ffi.from_handle(user_data)
    parser.on_event(event)
