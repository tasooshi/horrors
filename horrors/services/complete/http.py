import functools

from horrors import (
    services,
    triggers,
)

import flask
import flask_cors


__all__ = ['HTTPFlask']


class HTTPFlask(services.Service):

    address = '0.0.0.0'
    port = None

    def __init__(self, scenario, address=None, port=None, ssl_context=None):
        self.scenario = scenario
        self.ssl_context = ssl_context
        super().__init__(scenario, address, port)
        self.routes = dict()
        self.app = flask.Flask(__name__)
        flask_cors.CORS(self.app)

    def process_triggers(self):
        self.process(triggers.PathContains, flask.request.path)
        self.process(triggers.DataMatch, flask.request.data)

    def add_route(self, route, methods, content):
        self.routes[route] = (methods, content)

    def start_server(self):
        for route, view in self.routes.items():
            methods, content = view
            name = ''.join(ele for ele in route if ele.isalnum())
            if not callable(content):
                content = functools.partial(flask.render_template_string, content)
                content.__name__ = name
            self.app.add_url_rule(route, name, content, methods=methods)
        self.app.before_request(self.process_triggers)
        self.app.run(
            host=self.address,
            port=self.port,
            ssl_context=self.ssl_context
        )
