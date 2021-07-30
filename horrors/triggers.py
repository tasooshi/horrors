import re

from horrors import (
    events,
    logging,
)


class Trigger:

    def __init__(self, condition, bucket=None):
        self.condition = condition
        self.bucket = bucket

    def evaluate(self, data, event):
        logging.debug(f'Evaluating `{self.condition}` with data: {data}')


class DataMatch(Trigger):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.regex = re.compile(self.condition)

    async def evaluate(self, data, event):
        super().evaluate(data, event)
        match = self.regex.match(data)
        if match:
            logging.debug(f'Condition `{self.condition}` met with data: {data}')
            if self.bucket:
                events.Event.store[self.bucket] = match.groups()
                logging.debug(f'Bucket `{self.bucket}` contents: {events.Event.store[self.bucket]}')
            await events.Event.send(event)


class DataContains(Trigger):

    async def evaluate(self, data, event):
        super().evaluate(data, event)
        if self.condition in data:
            logging.debug(f'Condition `{self.condition}` met with data: {data}')
            await events.Event.send(event)


class PathContains(DataContains):

    pass


class UsernameContains(DataContains):

    pass


class PasswordContains(DataContains):

    pass
