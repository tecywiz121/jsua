'''
Provides a JSON parser that can begin parsing at any arbitrary point in a
stream, not necessarily at the beginning.
'''

from .parser import Parser
from .blob import Blob
from .pool import pool
