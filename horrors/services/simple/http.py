import email.utils
import http
import time

from horrors import (
    logging,
    events,
    services,
)


__all__ = ['HTTPStatic']


class HTTPStatic(services.Service):

    address = '127.0.0.1'
    port = 8888
    close_connection = True
    banner = 'HTTPStatic'
    template_404 = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Page not found</title></head><body><h1>404 Not Found!</h1></body></html>'

    def __init__(self, address=None, port=None):
        super().__init__(address, port)
        self.routes = dict()
        self.buffer = None

    def date_time_string(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        return email.utils.formatdate(timestamp, usegmt=True)

    def timestamp(self, request, sock):
        return str(time.time())

    def send_response(self, status_code=200):
        status_code = http.HTTPStatus(status_code)
        self.buffer = list()
        self.buffer.append(
            f'HTTP/1.1 {status_code.value} {status_code.phrase}\r\n'
        )

    def send_header(self, key, value):
        if self.buffer is None:
            raise RuntimeError('Must be initialized with `send_response` first')
        self.buffer.append(
            f'{key}: {value}\r\n'
        )

    def add_route(self, route, content):
        self.routes[route] = content

    def end_headers(self):
        if self.close_connection:
            self.send_header('Connection', 'close')
        self.buffer.append('\r\n')

    async def send_content(self, writer, content='', status_code=200, content_type='text/html'):
        if isinstance(content, str):
            content = content.encode('latin-1')
        self.send_response(status_code)
        self.send_header('Server', self.banner)
        self.send_header('Date', self.date_time_string())
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        full_response = ''.join(self.buffer)
        full_response = full_response.encode('latin-1')
        full_response += content
        writer.write(full_response)
        await writer.drain()
        writer.write_eof()
        writer.close()
        logging.debug(f'Sent response:\r\n{full_response}')

    async def handler(self, reader, writer):
        request = list()
        while True:
            data = await reader.readline()
            if not data or data == b'\r\n':
                break
            else:
                data = data.decode()
                self.process(events.DataMatch, data)
                logging.debug(rf'Received:\r\n{data}')
                request.append(data)
        try:
            path = request[0].split(' ')[1]
        except IndexError:
            await self.send_content(writer, content='Error!', status_code=500)
        else:
            self.process(events.PathContains, path)
            try:
                content = self.routes[path]
            except KeyError:
                await self.send_content(writer, content=self.template_404, status_code=404)
            else:
                if callable(content):
                    content = content(self, request, reader._transport._sock)
                if isinstance(content, bytes):
                    content_type = 'application/octet-stream'
                else:
                    content_type = 'text/html'
                await self.send_content(writer, content)
