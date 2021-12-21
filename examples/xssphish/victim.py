#!/usr/bin/env python3

import os

import http.server
import socketserver


DEFAULT_RESPONSE = open('victim.html').read()


class Victim(http.server.BaseHTTPRequestHandler):

    def send_content(self, status_code=200, content_type='text/html', location=None):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(DEFAULT_RESPONSE)))
        if location:
            self.send_header('Location', location)
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(bytes(DEFAULT_RESPONSE, 'utf-8'))
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
