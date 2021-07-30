import asyncio
import functools

from horrors import logging


class SceneOrdering(type):

    def __new__(cls, name, bases, attrs):
        if bases:
            funcs = [fun for fun in attrs.values() if callable(fun)]
            attrs['scenes'] = funcs
        return super().__new__(cls, name, bases, attrs)


class Scenario(metaclass=SceneOrdering):

    def __init__(self, **context):
        self.context = context
        self.loop = asyncio.get_event_loop()

    def debug(self):
        logging.init(logging.logging.DEBUG)

    def logged(self, func, args=None, kwargs=None):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            logging.info(f'Running `{func.__name__}`')
            return await func(*args, **kwargs)
        return wrapped(self)

    async def story(self):
        for scene in self.scenes:
            await self.logged(scene, args={self})

    def spawn(self, service):
        service._spawn(self.loop)

    def play(self):
        try:
            future = asyncio.gather(self.story(), return_exceptions=True)
            self.loop.run_until_complete(future)
        except KeyboardInterrupt:
            logging.info('Quitting...')
            future.cancel()
