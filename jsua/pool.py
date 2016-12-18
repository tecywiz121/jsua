from ._jsua import lib as _jsua, ffi
from collections.abc import Sequence

class _Buffer(Sequence):
    def __init__(self, size, data):
        self._owns = True
        self._size = size
        self._data = data

    @property
    def data(self):
        if self._owns:
            return self._data
        else:
            raise ValueError('buffer no longer owns data')

    def __len__(self):
        if self._owns:
            return self._size;
        else:
            raise ValueError('buffer no longer owns data')

    def _chkidx(self, key):
        if not self._owns:
            raise ValueError('buffer no longer owns data')

        if key < 0:
            raise KeyError('negative index not supported')

        if key >= self._size:
            raise IndexError('buffer index out of range')

    def __getitem__(self, key):
        self._chkidx(key)
        return self._data[key]

    def __setitem__(self, key, value):
        self._chkidx(key)
        self._data[key] = value

    def release(self):
        self._owns = False
        self._data = ffi.NULL
        self._size = 0

    def __del__(self):
        if self._owns:
            pool.give_back(self)

class MemoryPool(object):
    def __init__(self, chunk_size=1024, max_available=100):
        self._chunk_size = chunk_size
        self.available = []
        self.used = 0
        self.max_available = max_available

    @property
    def chunk_size(self):
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, v):
        if v != self._chunk_size:
            if self.used > 0:
                raise ValueError('changing chunk_size while blocks are allocated')
            for x in self.available:
                _jsua.unallocate_u8(x)
            self.available.clear()
            self._chunk_size = v

    def _take(self):
        self.used += 1
        try:
            return self.available.pop()
        except IndexError:
            pass

        result = _jsua.allocate_u8(self.chunk_size)
        if result == ffi.NULL:
            self.used -= 1
            raise MemoryError
        else:
            return result

    def take(self):
        return _Buffer(self._chunk_size, self._take())

    def give_back(self, buf):
        self.give_back(buf._data)
        buf.release()

    def _give_back(self, chunk):
        if self.used <= 0:
            raise ValueError('giving back an extra chunk')
        self.used -= 1
        if len(self.available) >= self.max_available:
            _jsua.unallocate_u8(chunk)
        else:
            self.available.append(chunk)

    def __del__(self):
        for x in self.available:
            _jsua.unallocate_u8(x)
        self.available.clear()

pool = MemoryPool()

@ffi.def_extern()
def pool_give_back(x):
    pool._give_back(ffi.cast('uint8_t *', x))

