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

    async def http_request(self, method, url, headers=None, **kwargs):
        request_headers = self.http_headers.copy()
        if headers:
            request_headers.update(headers)
        http_kwargs = self.http_kwargs
        if kwargs:
            http_kwargs.update(kwargs)
        async with aiohttp.ClientSession(headers=request_headers) as session:
            try:
                async with getattr(session, method)(url, **http_kwargs) as response:
                    content = await response.content.read()
                    return {'status': response.status, 'headers': dict(response.raw_headers), 'content': content}
            except aiohttp.ClientResponseError:
                logging.info(f'Request failed for {url}')

    async def http_get(self, url, headers=None):
        return await self.http_request('get', url, headers)

    async def http_post(self, url, data=None, headers=None):
        if data is None:
            data = {}
        return await self.http_request('post', url, headers, data=data)

    def register(self, service):
        self.services.append(service)

    def add_scene(self, scene, when=None):
        if when is None:
            when = self.scene_index
            self.scene_index += 1
        logging.debug(f'Scene {scene}, event: {when}')
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
        await asyncio.gather(*tasks, return_exceptions=True)

    def play(self):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            logging.info('Quitting...')
