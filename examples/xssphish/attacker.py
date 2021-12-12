#!/usr/bin/env python3

import os

from horrors import scenarios
from horrors.services.utility import collector


if __name__ == "__main__":

    badjs = open(os.path.join(os.path.dirname(__file__), 'fakequery.js')).read()

    story = scenarios.Scenario()
    
    httpd = collector.HTTPCollector(story)
    httpd.add_route('/', ['GET'], '<html><head><title>Test</title></head><body><h1>Test</h1></body></html>')
    httpd.add_route('/fakequery.js', ['GET'], badjs)
    httpd.add_route('/collect/', ['GET', 'POST'], httpd.collect)
    
    # story.debug()
    story.play()
