from jsua.parser import SynchronizingParser

import unittest
import io

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

        previous = 111
        while src:
            backing = io.BytesIO(src)
            parser = SynchronizingParser(backing)

            count = 0
            for _ in parser.parse():
                count += 1
                self.assertTrue(count <= previous)

            previous = count
            src = src[1:]
