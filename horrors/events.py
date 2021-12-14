import re

from horrors import logging


class Event:

    def __init__(self, condition, in_context=None):
        self.condition = condition
        self.in_context = in_context

    def evaluate(self, scenario, data, scene):
        logging.debug(f'Evaluating `{self.condition}` with data: {data}')


class DataMatch(Event):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.regex = re.compile(self.condition)

    def evaluate(self, scenario, data, scene):
        super().evaluate(scenario, data, scene)
        match = self.regex.match(data)
        if match:
            logging.debug(f'Condition `{self.condition}` met')
            if self.in_context:
                scenario.context[self.in_context] = match.groups()
                logging.debug(f'Context `{self.in_context}` contents: {scenario.context[self.in_context]}')
            logging.debug(f'Setting scene to `{scene}`')
            scenario.state = scene
        else:
            logging.debug(f'Condition `{self.condition}` NOT met')


class DataContains(Event):

    def evaluate(self, scenario, data, scene):
        super().evaluate(scenario, data, scene)
        if self.condition in data:
            logging.debug(f'Condition `{self.condition}` met with data: {data}, moving to {scene}')
            scenario.state = scene


class PathContains(DataContains):

    pass


class UsernameContains(DataContains):

    pass


class PasswordContains(DataContains):

    pass
