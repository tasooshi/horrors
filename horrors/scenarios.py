import asyncio
import functools

import aiohttp

from horrors import logging


class Scenario:

    TIMEOUT = 5
    SCENE_START = 1

    def __init__(self, **context):
        self.context = context
        self.scenes = list()
        self.services = list()
        self.scene_index = self.SCENE_START
        self.state = self.scene_index
        self.http_kwargs = dict()
        self.http_headers = dict()
        logging.init(logging.logging.INFO)

    def set_debug(self):
        logging.init(logging.logging.DEBUG)

    def watch_event(self, func, event):
        loop = asyncio.get_event_loop()
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            logging.info(f'Scene `{func.__name__}` is waiting for event `{event}`')
            while True:
                logging.debug('Current state: ' + str(self.state))
                if self.state == event:
                    result = await func(self)
                    logging.debug(f'Executed `{func.__name__}`')
                    if result:
                        self.state = result
                    else:
                        self.state = self.scene_index + 1
                else:
                    await asyncio.sleep(1)
        return wrapped

    def set_proxy(self, proxy):
        self.http_kwargs['proxy'] = proxy

    def set_headers(self, headers):
        self.http_headers = headers

    async def job(self, func, *args, **kwargs):
        func_call = functools.partial(func, *args, **kwargs)
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, func_call)
        try:
            return await asyncio.wait_for(future, self.TIMEOUT)
        except asyncio.TimeoutError:
            return False

    async def http_get(self, url, headers=None):
        if headers is None:
            headers = {}
        headers.update(self.http_headers)
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, **self.http_kwargs) as response:
                return await response.text()

    async def http_post(self, url, data=None, headers=None):
        if data is None:
            data = {}
        if headers is None:
            headers = {}
        headers.update(self.http_headers)
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=data, **self.http_kwargs) as response:
                return await response.text()

    def register(self, service):
        self.services.append(service)

    def add_scene(self, scene, when=None):
        if when is None:
            when = self.scene_index
            self.scene_index += 1
        logging.debug('Scene {}, event: {}'.format(scene, when))
        self.scenes.append(self.watch_event(scene, when))

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
        for scene in self.scenes:
            tasks.append(scene())
        await asyncio.gather(*tasks)

    def play(self):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            logging.info('Quitting...')
