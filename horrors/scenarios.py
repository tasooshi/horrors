import asyncio
import functools

from horrors import logging


class Scenario:

    STATE_CONTINUE = 'continue'
    TIMEOUT = 5

    def __init__(self, **context):
        self.context = context
        self.waiting = list()
        self.state = self.STATE_CONTINUE

    def debug(self):
        logging.init(logging.logging.DEBUG)

    def wait_for(self, func, state):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if state != self.STATE_CONTINUE:
                logging.info(f'Scene `{func.__name__}` is waiting for event `{state}`')
            while True:
                if self.state == state:
                    logging.info(f'Running `{func.__name__}`')
                    prev_state = self.state
                    result = await func(self)
                    logging.debug(f'Finished `{func.__name__}`')
                    if self.state == prev_state:
                        self.state = self.STATE_CONTINUE
                    return result
                else:
                    await asyncio.sleep(1)
        return wrapped

    async def background(self, func, *args, **kwargs):
        func_call = functools.partial(func, *args, **kwargs)
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, func_call)
        try:
            return await asyncio.wait_for(future, self.TIMEOUT, loop=loop)
        except asyncio.TimeoutError:
            return False

    def spawn(self, service):
        service._spawn(self)

    def add_scene(self, scene, when=STATE_CONTINUE):
        self.waiting.append(self.wait_for(scene, when))

    def play(self):
        loop = asyncio.get_event_loop()
        try:
            for scene in self.waiting:
                loop.run_until_complete(scene())
        except KeyboardInterrupt:
            logging.info('Quitting...')
            loop.close()
