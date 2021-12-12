import asyncio

from horrors import logging


class Service:

    address = None
    port = None

    def __init__(self, scenario, address=None, port=None):
        if address is not None:
            self.address = address
        if port is not None:
            self.port = port
        if self.address is None:
            raise RuntimeError('Missing `address` attribute')
        if self.port is None:
            raise RuntimeError('Missing `port` attribute')
        self.triggers = dict()
        self.scenario = scenario
        self.scenario.register(self)

    def set_event(self, state, when=None):
        if when is None:
            raise RuntimeError('Missing `when` keyword argument')
        self.triggers[type(when).__name__] = (state, when)

    def process(self, cls, data):
        if cls.__name__ in self.triggers:
            state, trigger = self.triggers[cls.__name__]
            trigger.evaluate(self.scenario, data, state)


from horrors.services.complete.http import *
from horrors.services.simple.ftp import *
from horrors.services.simple.http import *
from horrors.services.utility.collector import *
