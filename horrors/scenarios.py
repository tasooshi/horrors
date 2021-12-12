import asyncio
import functools

import aiohttp

from horrors import logging


class Scenario:

    TIMEOUT = 5
    SCENE_START = 1

    def __init__(self, **context):
        self.context = context
        self.waiting = list()
        self.services = list()
        self.scene_index = self.SCENE_START
        self.state = self.scene_index

    def debug(self):
        logging.init(logging.logging.DEBUG)

    def wait_for(self, func, state):
        loop = asyncio.get_event_loop()
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            logging.info(f'Scene `{func.__name__}` is waiting for event `{state}`')
            while True:
                logging.debug('Current state: ' + str(self.state))
                if self.state == state:
                    result = await func(self)
                    logging.debug(f'Executed `{func.__name__}`')
                    self.state = self.scene_index + 1
                    return result
                else:
                    await asyncio.sleep(1)
        return wrapped

    async def background(self, func, *args, **kwargs):
        func_call = functools.partial(func, *args, **kwargs)
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, func_call)
        try:
            return await asyncio.wait_for(future, self.TIMEOUT)
        except asyncio.TimeoutError:
            return False

    async def http_get(self, url, headers=None, proxy=''):
        if headers is None:
            headers = {}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, proxy=proxy) as response:
                return await response.text()

    async def http_post(self, url, data=None, headers=None, proxy=''):
        if data is None:
            data = {}
        if headers is None:
            headers = {}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=data, proxy=proxy) as response:
                return await response.text()

    def register(self, service):
        self.services.append(service)

    def add_scene(self, scene, when=None):
        if when is None:
            when = self.scene_index
            self.scene_index += 1
        logging.debug('Scene {}, index/event: {}'.format(scene, when))
        self.waiting.append(self.wait_for(scene, when))

    async def main(self):
        self.scene_index = self.SCENE_START
        tasks = list()
        for service in self.services:
            try:
                server = await asyncio.start_server(service.handler, service.address, service.port)
            except AttributeError:
                service.start_server()
            else:
                addr = server.sockets[0].getsockname()
                logging.info(f'Serving `{type(self).__name__}` on {addr[0]}:{addr[1]}')
                tasks.append(server.serve_forever())
        for trigger in self.waiting:
            tasks.append(trigger())
        await asyncio.gather(*tasks)

    def play(self):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            logging.info('Quitting...')
