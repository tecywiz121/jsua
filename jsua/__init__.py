'''
Provides a JSON parser that can begin parsing at any arbitrary point in a
stream, not necessarily at the beginning.
'''

from .parser import JSONEvent, JSONPart, SynchronizingParser, ParseError

def _main():
    '''
    USAGE: jsua [FILES...] [-]

        Parse FILES, or standard in if '-' is specified, and print 3-tuples
        representing the events emitted by the JSON parser.
    '''
    import sys

    def parse_file_like(f):
        p = SynchronizingParser(f)
        for state, event, value in p.parse():
            print('({:>7}, {:>12}, {!r})'.format(state.name,
                                                 event.name,
                                                 value))

    files = sys.argv[1:]
    if not files:
        files = ['-']

    for f in files:
        try:
            if '-' == f:
                parse_file_like(sys.stdin)
            else:
                with open(f, 'rb') as f:
                    parse_file_like(f)
        except ParseError as ex:
            sys.stderr.write('Parse Error: {}\n'.format(ex))
