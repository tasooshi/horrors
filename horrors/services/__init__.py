class Service:

    address = None
    port = None
    banner = 'Service'

    def __init__(self, address=None, port=None):
        if address is not None:
            self.address = address
        if port is not None:
            self.port = port
        if self.address is None:
            raise RuntimeError('Missing `address` attribute')
        if self.port is None:
            raise RuntimeError('Missing `port` attribute')
        self.events = dict()
        self.scenario = None

    def add_event(self, scene, when=None):
        if when is None:
            raise RuntimeError('Missing `when` keyword argument')
        self.events[type(when).__name__] = (scene, when)

    def process(self, cls, data):
        if cls.__name__ in self.events:
            scene, event = self.events[cls.__name__]
            event.evaluate(self.scenario, data, scene)


from horrors.services.complete.http import *
from horrors.services.simple.ftp import *
from horrors.services.simple.http import *
from horrors.services.utility.collector import *
