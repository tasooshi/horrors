import asyncio
import functools

import aiohttp

from horrors import logging


class Scenario:

    TIMEOUT = 5
    SCENE_START = 1

    def __init__(self, keep_running=True, **context):
        self.keep_running = keep_running
        self.context = context
        self.scenes = list()
        self.services = list()
        self.scene_index = self.SCENE_START
        self.scene_last = None
        self.state = self.scene_index
        self.http_kwargs = dict()
        self.http_headers = dict()
        logging.init(logging.logging.INFO)

    def set_debug(self):
        logging.init(logging.logging.DEBUG)

    def watch_state(self, obj):
        func = obj.task
        state = obj.when
        cls_name = obj.__class__.__name__
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            logging.info(f'Scene `{cls_name}` is waiting for state `{state}`')
            while True:
                logging.debug('Current state: ' + str(self.state))
                if self.state == state:
                    try:
                        await func()
                    except Exception as exc:
                        raise Exception(f'Scene `{cls_name}` raised exception {type(exc).__name__} at state `{state}`')
                    logging.info(f'Executed `{cls_name}`')
                    if self.state == self.scene_last and not self.keep_running:
                        raise asyncio.CancelledError
                    if obj.on_finish:
                        self.state = obj.on_finish
                    else:
                        self.scene_index += 1
                        self.state = self.scene_index
                    logging.debug(f'The new state is `{self.state}`')
                else:
                    await asyncio.sleep(1)
        return wrapped

    def set_proxy(self, proxy):
        self.http_kwargs['proxy'] = proxy

    def set_headers(self, headers):
        self.http_headers = headers

    def add_service(self, service):
        service.scenario = self
        self.services.append(service)

    def add_scene(self, scene_cls, when=None):
        if when is None:
            when = self.scene_index
            self.scene_index += 1
        self.scenes.append((self.watch_state(scene_cls(self, when)), when))
        logging.debug(f'Added scene {scene_cls.__name__} on state: {when}')

    async def main(self):
        try:
            self.scene_last = self.scenes[-1][1]
        except IndexError: 
            # NOTE: Should throw exception if that ever happens due to self.scene_last == None by default
            pass
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
            tasks.append(scene[0]())
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logging.info('End of story')

    def play(self):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            logging.info('Quitting...')


class Scene:

    on_finish = None

    def __init__(self, scenario, when):
        self.when = when
        self.scenario = scenario
        self.context = scenario.context

    async def http_request(self, method, url, headers=None, **kwargs):
        request_headers = self.scenario.http_headers.copy()
        if headers:
            request_headers.update(headers)
        http_kwargs = self.scenario.http_kwargs
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

    async def background(self, func, *args, **kwargs):
        func_call = functools.partial(func, *args, **kwargs)
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, func_call)
        try:
            return await asyncio.wait_for(future, self.TIMEOUT)
        except asyncio.TimeoutError:
            return False

    async def task(self):
        raise NotImplementedError
