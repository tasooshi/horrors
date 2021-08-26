import flask
import tinydb

from horrors.services.complete import http


class HTTPCollector(http.HTTPFlask):

    banner = 'HTTPCollector'
    template_200 = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>{banner}</title></head><body><pre>{content}</pre></body></html>'
    json_file = 'collected.json'

    def __init__(self, address=None, port=None, ssl_context=None):
        super().__init__(address, port, ssl_context)
        self.db = tinydb.TinyDB(self.json_file)

    def collect(self):
        data = dict(flask.request.values)
        self.db.insert(data)
        return flask.render_template_string(
            self.template_200.format(banner=self.banner, content=data)
        )
