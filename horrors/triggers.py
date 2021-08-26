import re

from horrors import logging


class Trigger:

    def __init__(self, condition, bucket=None):
        self.condition = condition
        self.bucket = bucket

    def evaluate(self, scenario, data, state):
        logging.debug(f'Evaluating `{self.condition}` with data: {data}')


class DataMatch(Trigger):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.regex = re.compile(self.condition)

    def evaluate(self, scenario, data, state):
        super().evaluate(scenario, data, state)
        match = self.regex.match(data)
        if match:
            logging.debug(f'Condition `{self.condition}` met')
            if self.bucket:
                scenario.context[self.bucket] = match.groups()
                logging.debug(f'Bucket `{self.bucket}` contents: {scenario.context[self.bucket]}')
            logging.debug(f'Setting state to `{state}`')
            scenario.state = state
        else:
            logging.debug(f'Condition `{self.condition}` NOT met')


class DataContains(Trigger):

    def evaluate(self, scenario, data, state):
        super().evaluate(scenario, data, state)
        if self.condition in data:
            logging.debug(f'Condition `{self.condition}` met with data: {data}')
            scenario.state = state


class PathContains(DataContains):

    pass


class UsernameContains(DataContains):

    pass


class PasswordContains(DataContains):

    pass
