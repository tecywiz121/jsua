'''
Parser for JSON streams capable of starting at an arbitrary location and
"figuring it out."
'''

import struct
from enum import Enum, unique
from .reader import Reader

class ParseError(Exception):
    '''Thrown when the parser encounters malformed JSON'''

@unique
class V(Enum):
    '''Enumeration representing a possibly unknown boolean value'''
    true = True
    false = False
    unknown = 'unknown'
    anti_unknown = '~unknown'

    def inverted(self):
        '''Returns the opposite of the current value'''
        if self == V.true:
            return V.false
        elif self == V.false:
            return V.true
        elif self == V.unknown:
            return V.anti_unknown
        elif self == V.anti_unknown:
            return V.unknown

    def __bool__(self):
        if self == V.true:
            return True
        elif self == V.false:
            return False
        else:
            raise TypeError('Cannot convert unknown value to boolean')

    def reify(self, v):
        '''Combine a given unknown or anti_unknown value with a constant'''
        if self in (V.true, V.false):
            raise TypeError('Cannot reify a true or false')
        elif self == V.unknown:
            return V.true if v else V.false
        elif self == V.anti_unknown:
            return V.false if v else V.true

@unique
class JSONPart(Enum):
    '''Represents a part of JSON'''
    unknown = 0
    object = 1
    array = 2
    string = 3
    number = 4

@unique
class JSONEvent(Enum):
    '''Describes a transition or event relevant to parsing JSON'''
    object_begin = 1
    object_end = 2

    array_begin = 4
    array_end = 5

    colon = 8
    comma = 9

    string = 10
    number = 11
    boolean = 12
    null = 13

class JSONStack:
    '''
    A stack that allows for 'unknown' values to be pushed, and later replaced
    when they are identified.
    '''
    def __init__(self):
        self.stack = [JSONPart.unknown]

    def push(self, part):
        '''Push part onto the stack'''
        if part not in JSONPart:
            raise Exception('Not a valid JSONPart')
        self.stack += [part]

    def pop(self, part):
        '''Pop part from the stack'''
        if part == JSONPart.unknown:
            raise Exception('Cannot pop an unknown JSONPart')

        current = self.stack[-1]
        if current == part:
            self.stack.pop()
        elif current != JSONPart.unknown:
            msg = 'Mismatched open/close. Expected {} but got {}.'
            raise ParseError(msg.format(current, part))

    def set(self, part):
        '''Replace the top of the stack with the given type'''
        current = self.stack[-1]
        if current == JSONPart.unknown:
            self.push(part)
        elif current != part:
            msg = 'Got character belonging to {}, but was in {}'
            raise ParseError(msg.format(part, current))

    def peek(self):
        '''Return the top of the stack without popping it'''
        return self.stack[-1]

class SynchronizingParser:
    '''A SAX-like parser that emits events for arbitrary JSON streams'''
    HEUR_STRING_YES = (b'\\', b"'")
    HEUR_STRING_NO = tuple(bytes([x]) for x in range(0, 0x20))
    HEUR_STRING_INVERT = (b'"',)
    HEUR_WHITESPACE = (b'\x09', b'\x0A', b'\x0D', b'\x20')
    HEUR_SYNCHRONIZE = HEUR_WHITESPACE + (b'[', b']', b'{', b'}',
                                          b',', b':', b'"')

    def __init__(self, src):
        self.src = Reader(src)

    def parse(self):
        '''
        Yields parse events as it makes its way through the JSON.
            yield (state, event, value)
        '''
        # Figure out if we're in a string or not
        self.src.mark()
        string = self._is_in_string()
        self.src.rewind()

        if string:
            self._skip_string()
        else:
            c = None
            while c not in self.HEUR_SYNCHRONIZE:
                first = self.src.first
                c = self.src.read()
            self.src.put_back(c, first)

        # Should be synchronized at this point; at least we know we aren't in
        # a string. Begin the parsing!

        stack = JSONStack()
        commas = 0
        previous = JSONPart.unknown

        while True:
            first = self.src.first

            try:
                c = self.src.read()
            except EOFError:
                if stack.peek() != JSONPart.unknown:
                    raise ParseError('Unterminated {}'.format(stack.peek()))
                break

            popped = None
            event = None
            value = None

            if b'{' == c:
                stack.push(JSONPart.object)
                event = JSONEvent.object_begin
            elif b'}' == c:
                popped = JSONPart.object
                event = JSONEvent.object_end
            elif b'[' == c:
                stack.push(JSONPart.array)
                event = JSONEvent.array_begin
            elif b']' == c:
                popped = JSONPart.array
                event = JSONEvent.array_end
            elif b':' == c:
                if previous not in (JSONPart.unknown, JSONPart.string):
                    raise ParseError('Invalid key type {}'.format(previous))
                stack.set(JSONPart.object)
                event = JSONEvent.colon
                commas = 0
            elif b',' == c:
                event = JSONEvent.comma
                if stack.peek() == JSONPart.unknown:
                    commas += 1
                    if commas >= 2:
                        commas = 0
                        stack.set(JSONPart.array)
            elif b'"' == c:
                popped = JSONPart.string
                event = JSONEvent.string
                value = self._parse_string()
            elif c in b'-0123456789':
                popped = JSONPart.number
                event = JSONEvent.number
                self.src.put_back(c, first)
                value = self._parse_number()
            elif c in self.HEUR_WHITESPACE:
                pass
            else:
                self.src.put_back(c, first)
                event, value = self._parse_const()


            if popped:
                previous = popped
                if popped in (JSONPart.array, JSONPart.object):
                    stack.pop(popped)
                    if stack.peek() == JSONPart.unknown:
                        commas = 0

            if event:
                yield (stack.peek(), event, value)

    def _parse_number(self):
        '''Reads bytes until the current number is ended'''
        v = b''

        try:
            first = self.src.first
            c = self.src.read()

            if c == b'-':
                v += c
                first = self.src.first
                c = self.src.read()

            # Leading zeros (except immediately before a decimal) aren't allowed
            # by the spec, but I'm going to accept them.

            while c in b'0123456789':
                v += c
                first = self.src.first
                c = self.src.read()

            if c == b'.':
                v += c
                first = self.src.first
                c = self.src.read()
                while c in b'0123456789':
                    v += c
                    first = self.src.first
                    c = self.src.read()

            if c in (b'e', b'E'):
                v += c
                first = self.src.first
                c = self.src.read()
                if c in b'+-0123456789':
                    v += c
                    first = self.src.first
                    c = self.src.read()
                else:
                    raise ParseError('Missing exponent')

            while c in b'0123456789':
                v += c
                first = self.src.first
                c = self.src.read()

            self.src.put_back(c, first)

            return float(v)
        except ValueError:
            raise ParseError('Malformed number literal')
        except EOFError:
            raise ParseError('Unterminated number literal')

    def _parse_const(self):
        '''Reads true, false, and null'''
        c = self.src.read()

        if c == b't':
            self._read_expect(b'rue')
            return (JSONEvent.boolean, True)
        elif c == b'f':
            self._read_expect(b'alse')
            return (JSONEvent.boolean, False)
        elif c == b'n':
            self._read_expect(b'ull')
            return (JSONEvent.null, False)
        else:
            raise ParseError('Unexpected character: {!r}'.format(c))

    def _read_expect(self, expected):
        '''Reads bytes, checking them against the expected byte object'''
        for e in expected:
            e = bytes([e])
            c = self.src.read()
            if e != c:
                raise ParseError('Expected {!r} but got {!r}'.format(e, c))

    def _read_unicode(self):
        '''Reads four digits'''
        try:
            r = b''
            for _ in range(4):
                c = self.src.read()
                if c not in b'0123456789ABCDEFabcdef':
                    raise ParseError('Invalid unicode sequence: {!r}'.format(c))
                r += c
            return struct.pack('<H', int(r, 16))
        except EOFError:
            raise ParseError('Incomplete unicode sequence')

    def _skip_string(self):
        '''Skips a string without parsing it.'''
        c = None
        p = None

        while c != b'"' or p == b'\\':
            p = c
            try:
                c = self.src.read()
            except EOFError:
                raise ParseError('Unterminated {}'.format(JSONPart.string))


    def _parse_string(self):
        '''Reads bytes until the current string is ended'''
        u16 = lambda q: bytes(q, 'utf-16le')

        result = b''
        c = None
        p = None

        while c != b'"' or p == b'\\':
            p = c
            try:
                c = self.src.read()
            except EOFError:
                raise ParseError('Unterminated {}'.format(JSONPart.string))

            if c in self.HEUR_STRING_NO:
                msg = 'Invalid character in string literal: {!r}'
                raise ParseError(msg.format(c))

            if p == b'\\':
                p = None

                if c == b'\\':
                    result += u16('\\')
                elif c == b'/':
                    result += u16('/')
                elif c == b'b':
                    result += u16('\b')
                elif c == b'f':
                    result += u16('\f')
                elif c == b'n':
                    result += u16('\n')
                elif c == b'r':
                    result += u16('\r')
                elif c == b't':
                    result += u16('\t')
                elif c == b'u':
                    result += self._read_unicode()
                elif c == b'"':
                    result += u16('"')
                else:
                    raise ParseError('Invalid backslash escape: {!r}'.format(c))
                c = None
            elif c != b'\\':
                result += bytes(str(c, 'utf-8'), 'utf-16le')

        return str(result, 'utf-16le')[:-1]

    def _is_in_string(self):
        '''Returns True if the current position is in a string literal'''
        result = V.unknown
        c = None
        p = None

        while result in (V.unknown, V.anti_unknown):
            first = self.src.first
            try:
                if c not in self.HEUR_WHITESPACE:
                    p = c

                c = self.src.read()
                if c in self.HEUR_STRING_YES:
                    result = result.reify(True)
                elif c in self.HEUR_STRING_NO:
                    result = result.reify(False)
                elif c in self.HEUR_STRING_INVERT:
                    result = result.inverted()
                elif p and p in b',' and c in b':]},':
                    result = result.reify(True)

            except EOFError:
                # In a properly formatted JSON file, strings must be closed by
                # the end of file.
                result = result.reify(False)

        return bool(result)
