from jsua.parser import SynchronizingParser, JSONEvent, JSONPart, V, ParseError

import unittest
import io

class VTest(unittest.TestCase):
    def test_inverted(self):
        self.assertEqual(V.true.inverted(), V.false)
        self.assertEqual(V.false.inverted(), V.true)
        self.assertEqual(V.unknown.inverted(), V.anti_unknown)
        self.assertEqual(V.anti_unknown.inverted(), V.unknown)

    def test_bool(self):
        self.assertTrue(bool(V.true))
        self.assertFalse(bool(V.false))
        with self.assertRaises(TypeError):
            bool(V.unknown)
        with self.assertRaises(TypeError):
            bool(V.anti_unknown)

    def test_reify(self):
        self.assertEqual(V.unknown.reify(True), V.true)
        self.assertEqual(V.unknown.reify(False), V.false)
        self.assertEqual(V.anti_unknown.reify(False), V.true)
        self.assertEqual(V.anti_unknown.reify(True), V.false)

        with self.assertRaises(TypeError):
            V.true.reify(True)

class ParserTest(unittest.TestCase):
    def setUp(self):
        backing = io.BytesIO(b'{"hello": "\\uD834\\uDD1E"}')
        self.parser = SynchronizingParser(backing)

    def test_parse(self):
        p = self.parser.parse()
        state, event, value = next(p)
        self.assertEqual(state, JSONPart.object)
        self.assertEqual(event, JSONEvent.object_begin)
        self.assertIsNone(value)

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.object)
        self.assertEqual(event, JSONEvent.string)
        self.assertEqual(value, 'hello')

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.object)
        self.assertEqual(event, JSONEvent.colon)
        self.assertIsNone(value)

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.object)
        self.assertEqual(event, JSONEvent.string)
        self.assertEqual(value, '\U0001D11E')

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.unknown)
        self.assertEqual(event, JSONEvent.object_end)
        self.assertIsNone(value)

        with self.assertRaises(StopIteration):
            next(p)

class ParserMismatched(unittest.TestCase):
    def test_arr_obj(self):
        backing = io.BytesIO(b'[}')
        p = SynchronizingParser(backing).parse()

        next(p)

        with self.assertRaises(ParseError):
            next(p)

    def test_obj_arr(self):
        backing = io.BytesIO(b'{]')
        p = SynchronizingParser(backing).parse()

        next(p)

        with self.assertRaises(ParseError):
            next(p)

    def test_colon_in_array(self):
        backing = io.BytesIO(b'[:')
        p = SynchronizingParser(backing).parse()

        next(p)

        with self.assertRaises(ParseError):
            next(p)

    def test_unterminated_array(self):
        backing = io.BytesIO(b'[')

        p = SynchronizingParser(backing).parse()

        next(p)

        with self.assertRaises(ParseError):
            next(p)

    def test_unterminated_object(self):
        backing = io.BytesIO(b'{')

        p = SynchronizingParser(backing).parse()

        next(p)

        with self.assertRaises(ParseError):
            next(p)

    def test_invalid_key(self):
        backing = io.BytesIO(b'{0:""}')

        p = SynchronizingParser(backing).parse()

        next(p)
        next(p)

        with self.assertRaises(ParseError):
            next(p)

    def test_two_commas(self):
        backing = io.BytesIO(b'9,8,')
        p = SynchronizingParser(backing).parse()

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.unknown)
        self.assertEqual(event, JSONEvent.comma)
        self.assertIsNone(value)

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.unknown)
        self.assertEqual(event, JSONEvent.number)
        self.assertEqual(value, 8.0)

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.array)
        self.assertEqual(event, JSONEvent.comma)
        self.assertIsNone(value)

    def test_two_commas_no_array(self):
        backing = io.BytesIO(b',8},')
        p = SynchronizingParser(backing).parse()

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.unknown)
        self.assertEqual(event, JSONEvent.comma)
        self.assertIsNone(value)

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.unknown)
        self.assertEqual(event, JSONEvent.number)
        self.assertEqual(value, 8.0)

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.unknown)
        self.assertEqual(event, JSONEvent.object_end)
        self.assertIsNone(value)

        state, event, value = next(p)
        self.assertEqual(state, JSONPart.unknown)
        self.assertEqual(event, JSONEvent.comma)
        self.assertIsNone(value)

    def test_malformed_number(self):
        backing = io.BytesIO(b',-.,')
        p = SynchronizingParser(backing).parse()

        next(p)
        with self.assertRaises(ParseError):
            next(p)

    def test_fakeout(self):
        backing = io.BytesIO(b',tp')
        p = SynchronizingParser(backing).parse()

        next(p)
        with self.assertRaises(ParseError):
            next(p)

    def test_unexpected_character(self):
        backing = io.BytesIO(b',p')
        p = SynchronizingParser(backing).parse()

        next(p)
        with self.assertRaises(ParseError):
            next(p)

    def test_missing_exponent(self):
        backing = io.BytesIO(b',8e,')
        p = SynchronizingParser(backing).parse()

        next(p)
        with self.assertRaises(ParseError):
            next(p)

    def test_unterminated_number(self):
        backing = io.BytesIO(b',8e')
        p = SynchronizingParser(backing).parse()

        next(p)
        with self.assertRaises(ParseError):
            next(p)

    def test_nonhex_unicode(self):
        backing = io.BytesIO(b'"\\uG')
        p = SynchronizingParser(backing).parse()

        with self.assertRaises(ParseError):
            next(p)

    def test_incomplete_unicode(self):
        backing = io.BytesIO(b'"\\u5')
        p = SynchronizingParser(backing).parse()

        with self.assertRaises(ParseError):
            next(p)

    def test_unterminated_string(self):
        backing = io.BytesIO(b'"\\')
        p = SynchronizingParser(backing).parse()

        with self.assertRaises(ParseError):
            next(p)

    def test_skip_unterminated(self):
        backing = io.BytesIO(b'\\b')
        p = SynchronizingParser(backing).parse()

        with self.assertRaises(ParseError):
            next(p)

    def test_escapes(self):
        backing = io.StringIO(r'"\\ \/ \b \f \n \r \t \""')
        p = SynchronizingParser(backing).parse()
        state, event, value = next(p)
        self.assertEqual(value, '\\ / \b \f \n \r \t "')
