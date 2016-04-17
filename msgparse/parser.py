"""Coroutines for extracting special symbols from chat messages

"""
import asyncio
import logging

from requests.exceptions import ConnectionError, HTTPError

from .cache import LRUCache
from .utils import (ident, unique, first, filterdict, immutable,
                    Pattern, HTML, HTTP, Tag, Response)


__all__ = ('parse_message',)

LOG = logging.getLogger(__name__)

#: How long to wait for net traffic when fetching titles
_NET_TIMEOUT = 1.0 # sec

#: _is_title(Element('<title   ./>)) -> True
_is_title = Tag.is_('title')

#: In a production setting this should be a caching service.
#: However, a LRUCache should suffice for demonstraions.
_cache = LRUCache()

#: Fields of the message response
Field = immutable('MessageFields',
    emoticons='emoticons',
    mentions='mentions',
    links='links',
)

@asyncio.coroutine
def _format_link(ctx, url):
    """Format the url as the dict containing both the url and title::

          >>> url = 'http://dillonhicks.io'
          >>> link = loop.run_until_complete(ctx, url)
          >>> print(link)
          {"title": "Dillon Hicks", "url": "http://dillonhicks.io"}

    If the url is not in the `msgparse.parser._cache` then this
    function will attempt to fetch and parse the HTML document from
    the given `url`.

    :param ctx: context object containing, at minimum,the asyncio loop
                and message config values.
    :param url: http url
    :returns: dict containing the url and the title or, on failure, None
    """

    if not Pattern.http_prefix.search(url):
        url = 'http://' + url

    entry = _cache.get(url)
    if entry is not None:
        return entry

    try:
        LOG.debug('Fetching url: %s', url)
        resp = yield from ctx.loop.run_in_executor(None, HTTP.get, url)

        if resp.status_code != HTTP.ok:
            # Short circut parsing possibly bogus content
            return None

    except Exception as e:
        LOG.debug('An error occured while fetching %s', url)

        # In a production setting, there may be different ways we want
        # to handle this. Do we add the None value to the cache for a
        # non 404? do we blacklist the url? etc.
        return None

    content_type = resp.headers.get('Content-Type', '')

    if Pattern.content_html.search(content_type) is None:
        # e.g. we will not try to parse mime-type/jpg for a title.

        LOG.debug('Skipping processing content of %s, it is not html', url)
        return None

    # Lazily and tteratively parse the XHTML document until we find the
    # first title tag and extract the text from that tag.
    tags = HTML.iter(resp.content)
    title = first(tag.text for tag in tags if _is_title(tag))

    if title is None:
        title = url[:16] + '...'

    link = {
        'url' : url,
        'title' : Pattern.multi_ws.sub(' ', title) # collapse running whitespace
    }

    _cache.set(url, link)
    return link


@asyncio.coroutine
def parse_message(ctx, content):
    """Parse a message to extract the list special symbols
    (see: `Field`).

    Each list corresponding to a special symbols are in the same order
    they were observed in the message content. Further, each special
    symbol list only contains the unqiue values for that symbol such
    that `len(set(symbols)) == len(symbols)`::

        >>> content = '(smile)(smile)(wow)(frown)(frown)(upvote)(smile)'
        >>> result = loop.run_until_complete(parse_message(cxt, content))
        >>> print(result[Field.emoticons] == ['smile', 'wow', 'frown', 'upvote'])
        True

    Note that parsing does no input validation. The calling context
    is responsible for the appropraite sanitation or truncation of
    content vis-à-vis performance.

    The one exception is urls. `parse_messages()` will only parse up
    to `ctx.message.max_urlrs' number of urls in order to have a sane
    default behavior.

    :param ctx: context object containing, at minimum,the asyncio loop
                and message config values.
    :param content:
    :type content: str

    :returns: json serialized dict of the lists of special symbols
    :rtype: str

    """
    LOG.debug('Parsing message; length: %s', len(content))

    # Create match generators of each of the special symbol types.
    mentions = (m.group() for m in Pattern.mention.finditer(content))
    emoticons = (m.group() for m in Pattern.emoticon.finditer(content))
    urls = (m.group() for m in Pattern.url.finditer(content))

    # Offload the link processing to separate coros since it might
    # require making a network call to fetch the title.
    fs = []
    for count, url in enumerate(unique(urls)):
        if count == ctx.message.max_urls:
            LOG.debug('Skipping further urls, content exceeded the max_number'
                      ' of urls max_urls: %s', ctx.message.max_urls)
            break

        coro = _format_link(ctx, url)
        fs.append(asyncio.ensure_future(coro))

    if len(fs) == 0:
        # asyncio.wait errors on empty lists.
        links = []
    else:
        done, pending = yield from asyncio.wait(fs, timeout=_NET_TIMEOUT)
        links = [f.result() for f in done if f.result() is not None]

        for f in pending:
            f.cancel()

    # Cohere the special symbols generators into a dict of unique lists
    # keyed by their symbol name.
    specials = {
        Field.mentions : list(unique(mentions)),
        Field.emoticons : list(unique(emoticons)),
        Field.links : links, # links are filtered on url before format
    }

    # Filter fields with empty lists
    specials = filterdict(specials)

    return Response.serialize(specials)
