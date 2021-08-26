import asyncio

from horrors import logging


class Service:

    address = None
    port = None

    def __init__(self, address=None, port=None):
        if address is not None:
            self.address = address
        if port is not None:
            self.port = port
        if self.address is None:
            raise RuntimeError('Missing `address` attribute')
        if self.port is None:
            raise RuntimeError('Missing `port` attribute')
        self.triggers = dict()
        self.scenario = None

    def set_event(self, state, when=None):
        if when is None:
            raise RuntimeError('Missing `when` keyword argument')
        self.triggers[type(when).__name__] = (state, when)

    def process(self, cls, data):
        if cls.__name__ in self.triggers:
            state, trigger = self.triggers[cls.__name__]
            trigger.evaluate(self.scenario, data, state)

    def _spawn(self, scenario, **kwargs):
        raise NotImplementedError

    def start_server(self):
        raise NotImplementedError


class SocketService(Service):

    address = None
    port = None

    async def start_server(self):
        server = await asyncio.start_server(self.handler, self.address, self.port)
        addr = server.sockets[0].getsockname()
        logging.info(f'Serving `{type(self).__name__}` on {addr[0]}:{addr[1]}')
        return server

    def _spawn(self, scenario, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.scenario = scenario
        loop.run_until_complete(self.start_server())
