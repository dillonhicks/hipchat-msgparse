import asyncio
import logging
import unittest

try:
    import simplejson as json
except ImportError:
    import json

from msgparse.utils import immutable
from msgparse.parser import Field, Link, parse_message

LOG = logging.getLogger(__name__)
MiB = 2 ** 20


class MessageParsingTests(unittest.TestCase):
    ctx = None

    @staticmethod
    def setUpClass():
        MessageParsingTests.ctx = immutable('Context', loop=asyncio.get_event_loop())

    @staticmethod
    def tearDownClass():
        MessageParsingTests.ctx.loop.close()

    def test_emoticon(self):
        emoticon = 'lolwut'
        content = '({})'.format(emoticon)
        parser = parse_message(self.ctx, content)
        result = json.loads(self.ctx.loop.run_until_complete(parser))

        assert len(result[Field.emoticons]) == 1
        assert result[Field.emoticons][0] == emoticon
        assert Field.links not in result
        assert Field.mentions not in result

        emoticon = '(123abc)'
        parser = parse_message(self.ctx, emoticon)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        assert len(result[Field.emoticons]) == 1

    def test_mention(self):

        mention = 'dillon'
        content = '@{}'.format(mention)
        parser = parse_message(self.ctx, content)
        result = json.loads(self.ctx.loop.run_until_complete(parser))

        assert len(result[Field.mentions]) == 1
        assert result[Field.mentions][0] == mention
        assert Field.links not in result
        assert Field.emoticons not in result

    def test_link(self):

        url = 'http://google.com'
        parser = parse_message(self.ctx, url)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)

        assert len(result[Field.links]) == 1
        assert result[Field.links][0][Link.url] == url
        assert result[Field.links][0][Link.title] is not None
        assert Field.emoticons not in result
        assert Field.mentions not in result

        # Ensure full uris work and not just domains
        url = 'http://dillonhicks.io/index.html'
        parser = parse_message(self.ctx, url)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result[Field.links]) == 1

        # This case IS NOT a failure case since the url regex still
        # matches google.com
        url = 'http:// google.com'
        parser = parse_message(self.ctx, url)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result[Field.links]) == 1

    def test_empty(self):
        content = ''
        parser = parse_message(self.ctx, content)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

    def test_no_specials(self):
        content = (
            'Resistance Is futile, lower your shields and prepare to be '
            'assimilated. As a drone, you will have no need of mentions or '
            'emoticons for we are all hyperlinked.')

        parser = parse_message(self.ctx, content)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

    def test_url_limit(self):
        max_urls = 1
        content = 'http://bitbucket.org http://google.com http://dillonhicks.io'
        parser = parse_message(self.ctx, content, max_urls=max_urls)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result[Field.links]) == max_urls

    @unittest.skip("Disabled by default")
    def test_big(self):
        with open('tests/monster.json', 'r') as inf:
            monster = json.load(inf)

        parser = parse_message(self.ctx, monster['content'])
        result = json.loads(self.ctx.loop.run_until_complete(parser))

        assert len(result[Field.links]) == self.ctx.message.max_urls
        assert len(result[Field.emoticons]) == monster['emoticons']
        assert len(result[Field.mentions]) == monster['mentions']

    def test_bad_links(self):
        """Test for bad links. In an idea world we would
        have mock for HTTP.get that would not reach out
        to the network."""
        url = 'http://C++.com'
        parser = parse_message(self.ctx, url)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        url = 'lol.c om'
        parser = parse_message(self.ctx, url)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        url = 'htt://lol._org'
        parser = parse_message(self.ctx, url)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        url = ''
        parser = parse_message(self.ctx, url)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        url = 'https://wubba.dubbalublub'
        parser = parse_message(self.ctx, url)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

    def test_bad_emoticons(self):

        # Too long
        emoticon = '(inagalaxyfarfarawaytherewasoneemoticontorulethemall)'
        parser = parse_message(self.ctx, emoticon)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        # Too short
        emoticon = '()'
        parser = parse_message(self.ctx, emoticon)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        # malformed - notalphanum
        emoticon = '(mal forma)'
        parser = parse_message(self.ctx, emoticon)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        # malformed - notalphanum
        emoticon = '(one+two)'
        parser = parse_message(self.ctx, emoticon)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

    def test_bad_mentions(self):
        # Too long
        mention = '@'
        parser = parse_message(self.ctx, mention)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        # Too short
        mention = '@bob+loblaw'
        parser = parse_message(self.ctx, mention)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result[Field.mentions])== 1
        assert result[Field.mentions][0] == 'bob'

        # malformed - notalphanum
        mention = '@+1'
        parser = parse_message(self.ctx, mention)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

        # malformed - allow _ but not -
        mention = '@-there-'
        parser = parse_message(self.ctx, mention)
        result = json.loads(self.ctx.loop.run_until_complete(parser))
        LOG.debug('%s', result)
        assert len(result) == 0

    def test_cmcg1(self):
        content = '@chris you around?'
        parser = parse_message(self.ctx, content)
        result = json.loads(self.ctx.loop.run_until_complete(parser))

        assert len(result[Field.mentions]) == 1
        assert result[Field.mentions] == ['chris']

    def test_cmcg2(self):
        content = "Good morning! (megusta) (coffee) (coffee) (coffee)"

        parser = parse_message(self.ctx, content)
        result = json.loads(self.ctx.loop.run_until_complete(parser))

        assert len(result[Field.emoticons]) == 2
        assert result[Field.emoticons] == ['megusta', 'coffee']

    def test_cmcg3(self):
        content = "Olympics are starting soon; http://www.nbcolympics.com"
        parser = parse_message(self.ctx, content)
        result = json.loads(self.ctx.loop.run_until_complete(parser))

        assert len(result[Field.links]) == 1
        assert result[Field.links][0][Link.url] == 'http://www.nbcolympics.com'
        assert result[Field.links][0][Link.title] is not None

    def test_cmcg4(self):
        content = ('@bob @john (success) such a cool feature; '
                  'https://twitter.com/jdorfman/status/430511497475670016')

        parser = parse_message(self.ctx, content)
        result = json.loads(self.ctx.loop.run_until_complete(parser))

        links = [
            {
                Link.url: 'https://twitter.com/jdorfman/status/430511497475670016',
                Link.title: ('Justin Dorfman on Twitter: "nice @littlebigdetail from '
                          '@HipChat (shows hex colors when pasted in chat). '
                          'http://t.co/7cI6Gjy5pq"')
            }
        ]

        assert result[Field.mentions] == ['bob', 'john']
        assert result[Field.emoticons] == ['success']
        assert result[Field.links] == links
