import flask
import tinydb

from horrors.services.complete import http


__all__ = ['HTTPCollector']


class HTTPCollector(http.HTTPFlask):

    address = '0.0.0.0'
    port = 8888
    banner = 'HTTPCollector'
    template_200 = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>{banner}</title></head><body><pre>{content}</pre></body></html>'
    json_file = 'collected.json'

    def __init__(self, scenario, address=None, port=None, ssl_context=None):
        self.scenario = scenario
        if address is None:
            address = self.address
        if port is None:
            port = self.port
        super().__init__(scenario, address, port, ssl_context)
        self.db = tinydb.TinyDB(self.json_file)

    def collect(self):
        data = dict(flask.request.values)
        self.db.insert(data)
        return flask.render_template_string(
            self.template_200.format(banner=self.banner, content=data)
        )
