'''
Utilities for reading binary file-like objects.
'''

class ReaderError(Exception):
    '''Thrown when a Reader is asked to perform an invalid operation'''

class Reader:
    '''Wrapper around a file-like object that supports mark-rewind semantics'''
    def __init__(self, source):
        self.source = source

        self.marking = False

        self.tape = []
        self.tape_first = True

        self.buffer = []

        self.first = True

    def mark(self):
        '''Starts copying bytes from the source into the rewind tape'''
        if self.marking:
            raise ReaderError('Stream already has mark set')
        self.tape_first = self.first
        self.marking = True

    def rewind(self):
        '''Simulates rewinding the source until the previously set mark'''
        if not self.marking:
            raise ReaderError('Stream has no mark set')
        self.marking = False
        self.tape.reverse()
        self.buffer += self.tape
        if self.tape_first:
            self.first = True
        self.tape = []

    def _read_one(self):
        '''Reads a single character, without updating the tape'''
        self.first = False
        if self.buffer:
            return self.buffer.pop()
        else:
            r = self.source.read(1)
            if len(r):
                if not isinstance(r, bytes):
                    r = bytes(r, 'utf-8')
                return r
            else:
                raise EOFError()

    def read(self):
        '''Reads a single byte from the source'''
        c = self._read_one()
        if self.marking:
            self.tape += [c]
        return c

    def peek(self):
        '''Reads a single byte without consuming it'''
        first = self.first
        c = self.read()
        self.put_back(c, first)
        return c

    def put_back(self, v, first):
        '''Put back a value to be read next'''
        self.first = first
        self.buffer += [v]
        self.tape = self.tape[:-1]

