"""
Grab bag of of utilites to assist in parsing and filtering content.
"""
import re
import functools

from io import BytesIO
from itertools import filterfalse
from enum import Enum
from collections import namedtuple

# 3rd Party Imports
import lxml.etree
import requests

try:
    import simplejson as json
except ImportError:
    import json

__all__ = (
    'HTML',
    'HTTP',
    'Pattern',
    'Response',
    'Tag',
    'ident',
    'unique',
    'immutable',
    'first',
    'filterdict'
)


def ident(f):
    """Identity function: f(x) = x"""
    return f


def first(iterable, or_=None):
    """Get the first element of an iterable.
    Just semantic sugar for next(it, None).
    """
    return next(iterable, or_)


def filterdict(d, func=ident):
    """Filter items in a dict based on func(item.value)
    :returns: a filtered copy of `d`
    """
    return { k : v for k, v in d.items() if func(v) }


def unique(iterable, key=ident):
    """Filter duplicates from an interable while keeping order::

          unique([1,1,1,2,2,2,3,4]) -> [1,2,3,4]

    :param iterable: The iterable to filter
    :param key: Function toextract the comparison
                key from elements in the iterable.
    :default key: `ident`

    """
    seen = set()

    for elem in iterable:
        k = key(elem)
        if k in seen:
            continue

        seen.add(k)
        yield elem


def immutable(clazz_name, **attrs):
    """Immutable object factory backed by a namedtuple. It is only truely
    immutable if the attributes are immutable as well.

    :param clazz_name: The name given to the namedtuple
    :param attrs: The attributes of the immutable object
    """
    clazz = namedtuple(clazz_name, attrs.keys())
    return clazz(**attrs)


class Pattern:
    """Regular expression for parsing or formatting"""

    #: @frank @sally @foo_bar_BAZ123
    mention = re.compile(r'(?<=[@])[\w]+')

    #: http://what.com, google.com
    url = re.compile(r"""
        (http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)
        | # or
        (\S+[.][a-zA-Z]{2,6})""", re.VERBOSE)

    #: (lol) (agree)
    emoticon = re.compile(r'(?<=[(])[a-zA-Z0-9]{1,15}(?=[)])')

    #: two or more whitespace symbols
    multi_ws = re.compile(r'\s\s+')

    #: http:// or https:// prefix
    http_prefix = re.compile(r'^http[s]?://')

    #: case insensitive pattern for
    content_html = re.compile(r'text/html', re.I)


class Response:
    #: Abstraction wrapper to allow for a single definition : of how
    #: responses are serialized. In this case, we use the json pretty
    #: print style (4 spaces per level of nesting).
    serialize = functools.partial(json.dumps, indent=4, separators=(',', ': '))

class HTTP:
    """HTTP constants and verb functions"""

    #: The good status code for HTTP responses
    ok = 200

     #: Asyncio friendly wrapper for requests.get with a timeout
    get = functools.partial(requests.get, timeout=2.0)


class HTML:
    """Utilities for interacting with HTML documents"""

    @staticmethod
    def iter(content):
        """Generates each element in the DOM of the HTML one element at a
        time. Will recover on failure. Unparsable documents become a
        single paragraph element containing the text of the content.
        """

        context = lxml.etree.iterparse(BytesIO(content), recover=True, html=True)

        for action, elem in context:
            yield elem


class Tag:
    """Utilities for HTML Tags"""

    @staticmethod
    def is_(tag):
        def matcher(element):
            return element.tag == tag

        return matcher
