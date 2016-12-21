'''
Provides a JSON parser that can begin parsing at any arbitrary point in a
stream, not necessarily at the beginning.
'''

from .parser import Parser, EventType, ParseError
from .blob import Blob
from .pool import pool

def _main():
    import sys

    events = {
        EventType.ARR_END:      b'ARR_END',
        EventType.ARR_START:    b'ARR_START',
        EventType.COLON:        b'COLON',
        EventType.COMMA:        b'COMMA',
        EventType.OBJ_END:      b'OBJ_END',
        EventType.OBJ_START:    b'OBJ_START',
        EventType.VAL_BOOL:     b'VAL_BOOL',
        EventType.VAL_NUM:      b'VAL_NUM',
        EventType.VAL_STR:      b'VAL_STR',
        EventType.VAL_NULL:     b'VAL_NULL'
    }

    class ExampleParser(Parser):
        def __init__(self, *args, **kwargs):
            super(ExampleParser, self).__init__(*args, **kwargs)
            self.first = True
            self.buf = sys.stdout.buffer

        def on_event(self, event):
            buf = self.buf
            if self.first:
                buf.write(events[event.type])
                buf.write(b' ')
                self.first = False

            if event.data:
                buf.write(event.data)

            if event.completed:
                buf.write(b'\n')
                self.first = True

    with open(sys.argv[1], 'rb') as f:
        parser = ExampleParser()

        sz = -1
        while sz:
            buf = pool.take()
            sz = buf.read_from(f.fileno())
            blob = Blob(buf, sz)
            parser.feed(blob)
