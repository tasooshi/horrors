#!/usr/bin/env python3

from horrors import (
    scenarios,
    services,
)


if __name__ == "__main__":

    httpd = services.HTTPCollector()
    httpd.add_route('/', ['GET'], '<html><head><title>Test</title></head><body><h1>Test</h1></body></html>')
    httpd.add_route('/fakequery.js', ['GET'], open('fakequery.js').read())
    httpd.add_route('/collect/', ['GET', 'POST'], httpd.collect)

    story = scenarios.Scenario()
    story.add_service(httpd)
    story.play()
