import uuid

from horrors import (
    services,
    events,
)

__all__ = ['HTTPSanic']


from sanic import (
    Sanic,
    response,
    views,
)


class HTTPSanic(services.Service):

    address = '127.0.0.1'
    port = 8888

    class HtmlView(views.HTTPMethodView):

        _content = None

        def html_response(self, request):
            return response.html(self._content)

        def get(self, request):
            return self.html_response(request)

        def post(self, request):
            return self.html_response(request)

    def __init__(self, address=None, port=None):
        super().__init__(address, port)
        self.routes = dict()
        self.app = Sanic(self.banner + '-' + str(uuid.uuid4()))
        self.app.register_middleware(self.process_events)

    def process_events(self, request):
        self.process(events.PathContains, request.path)
        self.process(events.DataMatch, request.body)

    def add_route(self, route, methods, content):
        self.routes[route] = (methods, content)

    def response_factory(self, content):
        return self.HtmlView.as_view()

    def start_server(self):
        for route, view in self.routes.items():
            methods, content = view
            if not callable(content):
                # NOTE: This is a nasty hack around the issues related to using partials
                #       in routes definitions and generally magic that happens there and which
                #       complete understanding is currently not a priority
                view_cls = type('HtmlView', self.HtmlView.__bases__, dict(self.HtmlView.__dict__))
                setattr(view_cls, '_content', content)
                content = view_cls.as_view()
            self.app.add_route(content, route, methods)

        return self.app.create_server(
            host=self.address,
            port=self.port,
            return_asyncio_server=True,
            debug=self.scenario.debug
        )
