"""Simple in memory caching"""
import logging
from collections import OrderedDict

__all__ = ('LRUCache',)

LOG = logging.getLogger(__name__)

class _EntryMissing(object):
    def __repr__(self):
        return '<Entry: Missing>'

#: Internal sentinel value to represent a cache miss
#: such that None is still a valid entry.
_MISSING = _EntryMissing()

class LRUCache:
    """Fixed size LRUCache backed by an OrderedDict.

    .. note:: LRUCache is not threadsafe.
    """

    def __init__(self, max_size=128):
        """
        :param max_size: The max number of entries in the cache.
        """
        self.max_size = max_size
        self.queue = OrderedDict()

    def get(self, key):
        """ Get a cache entry
        :param key: the entry's hashable key
        :returns: entry if present else None
        """
        value = self.queue.get(key, _MISSING)

        if value is not _MISSING:
            LOG.debug('Cache hit for key: %s; value: %s', key, value)
            self.queue.move_to_end(key)
            return value

        LOG.debug('Cache miss for key: %s', key)
        return None

    def set(self, key, value):
        """Set a cache entry. If the number of entries exceends the max_size,
        then `set` will evict items from the cache until it equal to
        max_size.

        :param key: the entry's hashable key
        :param value:
        """

        prev = self.queue.pop(key, _MISSING)

        LOG.debug('Set key: %s; value: %s; prev: %s', key, value, prev)
        self.queue[key] = value

        LOG.debug('Cache size: %s', len(self.queue))
        while len(self.queue) > self.max_size:
            self.queue.popitem(last=False)


    def clear(self):
        """Clear the cache"""
        LOG.debug('Clear cache, size: %s', len(self.queue))
        self.queue = OrderedDict()
