import asyncio

from horrors import logging


class Event:

    events = dict()
    store = dict()

    @classmethod
    def get_event(cls, event):
        if event not in cls.events:
            logging.debug(f'Registered `{event}` event')
            cls.events[event] = asyncio.Event()
        return cls.events[event]

    @classmethod
    async def send(cls, event):
        obj = cls.get_event(event)
        logging.debug('Sent `{}` event'.format(event))
        obj.set()

    @classmethod
    async def wait(cls, event):
        obj = cls.get_event(event)
        logging.info('Waiting for `{}` event'.format(event))
        await obj.wait()

    @classmethod
    def lookup(cls, bucket):
        if bucket in cls.store:
            return cls.store[bucket]
        else:
            raise Exception('Item not found')
