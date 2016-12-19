from jsua import Parser, pool, Blob
from jsua.parser import Event, EventType

import unittest
import io

class TestParser(Parser):
    def __init__(self):
        super().__init__()
        self.events = []

    def on_event(self, event):
        self.events.append(event)

    def feed_all(self, src):
        pool.chunk_size = len(src)
        buf = pool.take()
        for idx, v in enumerate(src):
            buf[idx] = v
        blob = Blob(buf, len(src))
        self.feed(blob)
        self.feed(Blob())


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = TestParser()

    def test_parse(self):
        expected = (
            Event(EventType.OBJ_START,  True, None),
            Event(EventType.VAL_STR,    True, b'hello'),
            Event(EventType.COLON,      True, None),
            Event(EventType.VAL_STR,    True, b'\\uD834\\uDD1E'),
            Event(EventType.OBJ_END,    True, None)
        )
        self.parser.feed_all(b'{"hello": "\\uD834\\uDD1E"}')
        self.assertSequenceEqual(expected, self.parser.events)

    def test_arr_obj(self):
        expected = (
            Event(EventType.ARR_START,  True, None),
            Event(EventType.OBJ_END,    True, None),
        )
        self.parser.feed_all(b'[}')
        self.assertSequenceEqual(expected, self.parser.events)

    def test_obj_arr(self):
        expected = (
            Event(EventType.OBJ_START,  True, None),
            Event(EventType.ARR_END,    True, None),
        )
        self.parser.feed_all(b'{]')
        self.assertSequenceEqual(expected, self.parser.events)

    def test_colon_in_array(self):
        expected = (
            Event(EventType.OBJ_START,  True, None),
            Event(EventType.ARR_END,    True, None),
        )
        self.parser.feed_all(b'{]')
        self.assertSequenceEqual(expected, self.parser.events)

    def test_escapes(self):
        expected = (
            Event(EventType.VAL_STR,    True, r'\\ \/ \b \f \n \r \t \"'.encode('utf-8')),
            Event(EventType.COMMA,      True, None),
        )
        self.parser.feed_all(r'"\\ \/ \b \f \n \r \t \"",'.encode('utf-8'))
        self.assertSequenceEqual(expected, self.parser.events)
