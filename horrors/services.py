import asyncio
import email.utils
import http
import time

from horrors import (
    logging,
    triggers,
)


class Service:

    address = None
    port = None

    def __init__(self, address=None, port=None):
        if address is not None:
            self.address = address
        if port is not None:
            self.port = port
        if self.address is None:
            raise RuntimeError('Missing `address` attribute')
        if self.port is None:
            raise RuntimeError('Missing `port` attribute')
        self.triggers = dict()

    async def start_server(self):
        server = await asyncio.start_server(self.handler, self.address, self.port)
        addr = server.sockets[0].getsockname()
        logging.info(f'Serving `{type(self).__name__}` on {addr[0]}:{addr[1]}')
        return server

    def send(self, event, when=None):
        if when is None:
            raise RuntimeError('Missing `when` keyword argument')
        self.triggers[type(when).__name__] = (event, when)

    async def process(self, cls, data):
        if cls.__name__ in self.triggers:
            event, trigger = self.triggers[cls.__name__]
            await trigger.evaluate(data, event)

    def _spawn(self, loop):
        loop.run_until_complete(self.start_server())


class FTPReader(Service):

    address = ''
    port = 2121
    banner = 'FTPReader'

    async def handler(self, reader, writer):
        writer.write(b'220 ' + bytes(self.banner, 'latin-1') + b'\r\n')
        await writer.drain()
        while True:
            line = await reader.readline()
            if not line:
                break
            data = line.decode()
            logging.debug(rf'Received:\r\n{data}')
            if data.startswith('USER'):
                await self.process(triggers.UsernameContains, data)
                writer.write(b'331 Enter password\r\n')
            elif data.startswith('PASS'):
                await self.process(triggers.PasswordContains, data)
                writer.write(b'250 Okay\r\n')
            elif data.startswith('SYST'):
                writer.write(b'215 Windows_NT\r\n')
            elif data.startswith('RETR'):
                await self.process(triggers.DataMatch, data)
                writer.write(b'230 Continue\r\n')
            elif data.startswith('CWD'):
                await self.process(triggers.DataMatch, data)
                writer.write(b'250 Okay\r\n')
            elif data.startswith('QUIT'):
                writer.write(b'221 Goodbye!\r\n')
                await writer.drain()
                break
            await writer.drain()
        writer.close()


class HTTPStatic(Service):

    address = ''
    port = 8888
    close_connection = True
    banner = 'HTTPStatic'
    template_404 = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Page not found</title></head><body><h1>404 Not Found!</h1></body></html>'

    def __init__(self, routes=None, address=None, port=None):
        super().__init__(address, port)
        if routes is None:
            raise RuntimeError('Argument `routes` must be provided')
        else:
            self.routes = routes
        self.buffer = None

    def date_time_string(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        return email.utils.formatdate(timestamp, usegmt=True)

    def timestamp(self):
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

    def end_headers(self):
        if self.close_connection:
            self.send_header('Connection', 'close')
        self.buffer.append('\r\n')

    async def send_content(self, writer, content='', status_code=200, content_type='text/html'):
        self.send_response(status_code)
        self.send_header('Server', self.banner)
        self.send_header('Date', self.date_time_string())
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.buffer.append(content)
        full_response = ''.join(self.buffer)
        writer.write(bytes(full_response, 'latin-1'))
        await writer.drain()
        writer.close()
        logging.debug(f'Sent response:\r\n{full_response}')

    async def handler(self, reader, writer):
        request = list()
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break
            else:
                data = line.decode('latin-1').rstrip()
                request.append(data)
                logging.debug(rf'Received:\r\n{data}')
        path = request[0].split(' ')[1]
        await self.process(triggers.PathContains, path)
        try:
            content = self.routes[path]
        except KeyError:
            await self.send_content(writer, content=self.template_404, status_code=404)
        else:
            if callable(content):
                content = content(self)
            await self.send_content(writer, content)
