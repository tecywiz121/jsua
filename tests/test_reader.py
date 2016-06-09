from jsua.reader import Reader, ReaderError

import unittest
import io

class TestReader(unittest.TestCase):
    def setUp(self):
        backing = io.BytesIO(b'Hello World')
        self.reader = Reader(backing)

    def test_read_one_first(self):
        self.assertTrue(self.reader.first)
        self.assertEqual(self.reader._read_one(), b'H')
        self.assertFalse(self.reader.first)

    def test_read_one(self):
        self.assertEqual(self.reader._read_one(), b'H')
        self.assertEqual(self.reader._read_one(), b'e')
        self.assertEqual(self.reader._read_one(), b'l')
        self.assertEqual(self.reader._read_one(), b'l')
        self.assertEqual(self.reader._read_one(), b'o')
        self.assertEqual(self.reader._read_one(), b' ')
        self.assertEqual(self.reader._read_one(), b'W')
        self.assertEqual(self.reader._read_one(), b'o')
        self.assertEqual(self.reader._read_one(), b'r')
        self.assertEqual(self.reader._read_one(), b'l')
        self.assertEqual(self.reader._read_one(), b'd')

        with self.assertRaises(EOFError):
            self.reader._read_one()

    def test_read_one_buffered(self):
        self.reader.buffer = [b'X']
        self.assertEqual(self.reader._read_one(), b'X')
        self.assertEqual(self.reader._read_one(), b'H')

    def test_peek(self):
        self.assertEqual(self.reader.peek(), b'H')
        self.assertEqual(self.reader._read_one(), b'H')
        self.assertEqual(self.reader._read_one(), b'e')

    def test_peek_buffered(self):
        self.reader.buffer = [b'X']
        self.assertEqual(self.reader.peek(), b'X')
        self.assertEqual(self.reader._read_one(), b'X')
        self.assertEqual(self.reader._read_one(), b'H')

    def test_mark_double(self):
        self.reader.mark()
        with self.assertRaises(ReaderError):
            self.reader.mark()

    def test_rewind_unset(self):
        with self.assertRaises(ReaderError):
            self.reader.rewind()

    def test_mark_rewind_first(self):
        self.reader.mark()
        self.reader.read()
        self.assertFalse(self.reader.first)
        self.reader.rewind()
        self.assertTrue(self.reader.first)

    def test_mark_rewind(self):
        self.assertTrue(self.reader.first)
        self.assertEqual(self.reader.read(), b'H')
        self.assertFalse(self.reader.first)

        self.reader.mark()
        self.assertEqual(self.reader.read(), b'e')
        self.assertEqual(self.reader.read(), b'l')
        self.assertEqual(self.reader.peek(), b'l')
        self.assertEqual(self.reader.read(), b'l')
        self.assertEqual(self.reader.read(), b'o')
        self.reader.rewind()
        self.assertFalse(self.reader.first)
        self.assertEqual(self.reader.read(), b'e')
        self.assertEqual(self.reader.read(), b'l')
        self.assertEqual(self.reader.peek(), b'l')
        self.assertEqual(self.reader.read(), b'l')
        self.assertEqual(self.reader.read(), b'o')

    def test_put_back_not_first(self):
        self.reader.put_back(b'X', False)
        self.assertFalse(self.reader.first)
        self.assertEqual(self.reader.read(), b'X')
        self.assertFalse(self.reader.first)

    def test_put_back(self):
        self.reader.put_back(b'X', True)
        self.assertTrue(self.reader.first)
        self.assertEqual(self.reader.read(), b'X')
        self.assertFalse(self.reader.first)
        self.assertEqual(self.reader.read(), b'H')

    def test_mark_put_back_rewind(self):
        self.reader.mark()
        self.reader.put_back(b'X', True)
        self.assertTrue(self.reader.first)
        self.assertEqual(self.reader.peek(), b'X')
        self.assertTrue(self.reader.first)
        self.assertEqual(self.reader.read(), b'X')
        self.assertFalse(self.reader.first)
        self.assertEqual(self.reader.read(), b'H')
        self.reader.rewind()
        self.assertEqual(self.reader.read(), b'X')
        self.assertEqual(self.reader.read(), b'H')

class TestReaderString(TestReader):
    def setUp(self):
        backing = io.StringIO('Hello World')
        self.reader = Reader(backing)
