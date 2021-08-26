import functools

from horrors import (
    services,
    triggers,
)

import flask
import flask_cors


class HTTPFlask(services.Service):

    address = '0.0.0.0'
    port = None

    def __init__(self, address=None, port=None, ssl_context=None):
        self.ssl_context = ssl_context
        if port is None and self.ssl_context is None:
            port = 80
        else:
            port = 443
        super().__init__(address, port)
        self.routes = dict()
        self.app = flask.Flask(__name__)
        flask_cors.CORS(self.app)

    def process_triggers(self):
        self.process(triggers.PathContains, flask.request.path)
        self.process(triggers.DataMatch, flask.request.data)

    def _spawn(self, scenario, **kwargs):
        self.scenario = scenario
        for route, view in self.routes.items():
            methods, content = view
            name = ''.join(ele for ele in route if ele.isalnum())
            if not callable(content):
                content = functools.partial(flask.render_template_string, content)
                content.__name__ = name
            self.app.add_url_rule(route, name, content, methods=methods)
        self.app.before_request(self.process_triggers)
        self.start_server()

    def add_route(self, route, methods, content):
        self.routes[route] = (methods, content)

    def start_server(self):
        self.app.run(
            host=self.address,
            port=self.port,
            ssl_context=self.ssl_context
        )
