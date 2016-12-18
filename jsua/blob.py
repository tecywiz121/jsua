from ._jsua import lib as _jsua, ffi
from .pool import pool, pool_give_back

class Blob(object):
    def __init__(self, buf=None, size=0):
        self._size = size
        self._owns = True

        self._ptr = _jsua.jsua_blob_new()
        if ffi.NULL == self._ptr:
            raise MemoryError

        if size and buf:
            data = buf.data
            buf.release()
            _jsua.jsua_blob_init_take(self._ptr,
                                      data,
                                      size,
                                      _jsua.pool_give_back)
        else:
            _jsua.jsua_blob_init_empty(self._ptr)

    def release(self):
        self._owns = False
        self._ptr = ffi.NULL
        self._size = 0

    def __del__(self):
        if self._owns:
            self._owns = False
            _jsua.jsua_blob_fini(self._ptr)
            _jsua.jsua_blob_free(self._ptr)
