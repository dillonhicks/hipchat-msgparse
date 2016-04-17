"""
asyncio socket server for handling messages
"""
import os
import asyncio
import logging

from .parser import parse_message

__all__ = ('runserver', )

LOG = logging.getLogger(__name__)

class MessageProtocol(asyncio.Protocol):
    """
    Takes the recv'd bytes and parses it with the
    message handler. In real context this might be
    http or some handle rolled RPC frame.
    """
    def __init__(self, ctx):
        self.ctx = ctx

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        message = data.decode()[:self.ctx.message.max_size]

        f = asyncio.ensure_future(parse_message(self.ctx, message))
        f.add_done_callback(self.respond)

    def respond(self, f):
        message = f.result() + '\n'
        self.transport.write(message.encode())


def runserver(ctx, path='/tmp/msgparser.sock'):
    """
    Simple server to test msgparser over unix domain socket
    with socat:

      $ socat - UNIX-CONNECT:/tmp/msgparser.sock
      @helloworld (coffee) (sandwich) coffee.com
      {
        "mentions": [
           "helloworld"
        ],
        "emoticons": [
           "coffee",
           "sandwich"
        ],
        "links": [
            {
               "title": "Peet's Coffee & Tea",
               "url": "http://coffee.com"
            }
         ]
      }
    """

    coro = ctx.loop.create_unix_server(lambda : MessageProtocol(ctx), path=path)
    server = ctx.loop.run_until_complete(coro)

    LOG.debug('Server listening at path: %s', path)

    try:
        ctx.loop.run_forever()
    except KeyboardInterrupt:
        pass

    LOG.debug('Shutting down server')

    server.close()
    ctx.loop.run_until_complete(server.wait_closed())
    os.remove(path)
