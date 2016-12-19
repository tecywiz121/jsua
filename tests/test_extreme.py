from jsua import Parser, pool, Blob

import unittest
import io

class TestParser(Parser):
    def __init__(self):
        super().__init__()
        self.count = 0

    def on_event(self, event):
        self.count += 1

class TestExtreme(unittest.TestCase):
    def test_object(self):
        src = '''{
    "k1": true,
    "k2": false,
    "k3": null,
    "k4": -4.45e+7,
    "k5": [],
    "k6": [true],
    "k7": [false],
    "k8": [null],
    "k9": [-4.45e+7],
    "kA": [[],[]],
    "kB": {},
    "kC": {"j1": true},
    "kD": {"j1": false},
    "kE": {"j1": null},
    "kF": {"j1": -4.45e+7},
    "kG": {"j1": []},
    "kH": {"j1": {}}
}'''.encode('utf-8')

        previous = 114
        while src:
            parser = TestParser()
            pool.chunk_size = len(src)
            buf = pool.take()

            for idx, x in enumerate(src):
                buf[idx] = x

            blob = Blob(buf, len(src))
            parser.feed(blob)
            parser.feed(Blob())

            self.assertLessEqual(parser.count, previous)

            previous = parser.count

            del parser

            self.assertEqual(pool.used, 0)
            src = src[1:]
