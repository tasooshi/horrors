#!/usr/bin/env python3

import os

import http.server
import socketserver


class Victim(http.server.BaseHTTPRequestHandler):

    DEFAULT_RESPONSE = open(os.path.join(os.path.dirname(__file__), 'victim.html')).read()

    def send_content(self, status_code=200, content_type='text/html', content=DEFAULT_RESPONSE, location=None):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        if location:
            self.send_header('Location', location)
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(bytes(content, 'utf-8'))
        self.wfile.flush()

    def do_GET(self):
        self.send_content()

    def do_POST(self):
        self.send_content(
            status_code=303,
            location='http://127.0.0.1:8008/?message=Invalid credentials'
        )


example = socketserver.TCPServer(('127.0.0.1', 8008), Victim)
example.serve_forever()
