import asyncio
import concurrent.futures
import functools
import threading

import aiohttp
from sanic.server import async_server

from horrors import (
    logging,
    services,
)


class Scenario:

    def __init__(self, context=None, keep_running=True, interval=1, http_headers=None, http_proxy=None, debug=False, scene_start=1):
        self.context = context
        self.keep_running = keep_running
        self.interval = interval
        self.http_headers = dict() if http_headers is None else http_headers
        self.http_kwargs = dict()
        if http_proxy:
            self.http_kwargs['proxy'] = http_proxy
        self.debug = debug
        if debug:
            logging.init(logging.logging.DEBUG)
        else:
            logging.init(logging.logging.INFO)
        self.scenes = list()
        self.services = list()
        self.tasks = list()
        self.scene_start = scene_start
        self.scene_index = self.scene_start
        self.scene_last = None
        self.state = self.scene_index

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
                    if obj.next_event:
                        self.state = obj.next_event
                    else:
                        self.scene_index += 1
                        self.state = self.scene_index
                    logging.debug(f'The new state is `{self.state}`')
                else:
                    await asyncio.sleep(self.interval)
        return wrapped

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
        self.scene_index = self.scene_start
        self.tasks = list()
        for service in self.services:
            server = None
            if hasattr(service, 'handler'):
                server = await asyncio.start_server(service.handler, service.address, service.port)
            elif issubclass(type(service), services.HTTPSanic):
                server = await service.start_server()
                await server.startup()
            if server:
                logging.info(f'Serving `{type(service).__name__}` on {service.address}:{service.port}')
                self.tasks.append(asyncio.create_task(server.serve_forever()))
            else:
                logging.error(f'Failed starting `{type(service).__name__}` on {service.address}:{service.port}')
        for scene in self.scenes:
            self.tasks.append(asyncio.create_task(scene[0]()))
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logging.info('End of story')

    def play(self):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            logging.info('Quitting...')

    def stop(self):
        for task in self.tasks:
            task.cancel()


class Scene:

    next_event = None

    def __init__(self, scenario, when, timeout=5):
        self.when = when
        self.scenario = scenario
        self.context = scenario.context
        self.timeout = timeout

    def background(self, func, *args, **kwargs):
        thread = threading.Thread(None, func, args=args, kwargs=kwargs, daemon=True)
        thread.start()

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

    async def task(self):
        raise NotImplementedError
