from sanic import response
import tinydb

from horrors.services.complete import http


__all__ = ['HTTPCollector']


class HTTPCollector(http.HTTPSanic):

    banner = 'HTTPCollector'
    template_200 = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>{banner}</title></head><body><pre>{content}</pre></body></html>'
    json_file = 'collected.json'

    def __init__(self, address=None, port=None):
        super().__init__(address, port)
        self.db = tinydb.TinyDB(self.json_file)

    def collect(self, request):
        doc = dict()
        query = request.get_args()
        if query:
            doc['query'] = query
        body = dict(request.form)
        if body:
            doc['body'] = body
        doc['url'] = request.url
        doc['headers'] = dict(request.headers)
        doc['socket'] = {'ip': request.socket[0], 'port': request.socket[1]}
        self.db.insert(doc)
        return response.html(
            self.template_200.format(banner=self.banner, content=doc)
        )
