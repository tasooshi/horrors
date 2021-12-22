import os

from sanic import Sanic
import pytest

from horrors import (
    scenarios,
    services,
)


Sanic.test_mode = True


class Stop(scenarios.Scene):

    async def task(self):
        self.scenario.stop()


class HttpGet(scenarios.Scene):

    async def task(self):
        await self.http_get(
            'http://127.0.0.1:8888/collect/?test=http_get'
        )


class HttpPost(scenarios.Scene):

    async def task(self):
        await self.http_post(
            'http://127.0.0.1:8888/collect/',
            {'test': 'http_post'},
            {'Content-Type': 'application/x-www-form-urlencoded'}
        )


class HttpGetProxy(scenarios.Scene):

    async def task(self):
        # This should never reach the destination
        await self.http_get(
            'http://127.0.0.1/collect/?test=http_proxy'
        )


def test_http_get():
    httpd = services.HTTPCollector()
    httpd.add_route('/collect/', ['GET', 'POST'], httpd.collect)
    story = scenarios.Scenario(interval=0)
    story.add_scene(HttpGet)
    story.add_scene(Stop)
    story.add_service(httpd)
    story.play()
    with open(httpd.json_file, 'r') as fil:
        contents = fil.read()
        assert 'http_get' in contents
    os.remove(httpd.json_file)


def test_http_post():
    httpd = services.HTTPCollector()
    httpd.add_route('/collect/', ['GET', 'POST'], httpd.collect)
    story = scenarios.Scenario(interval=0)
    story.add_scene(HttpPost)
    story.add_scene(Stop)
    story.add_service(httpd)
    story.play()
    with open(httpd.json_file, 'r') as fil:
        contents = fil.read()
        assert 'http_post' in contents
    os.remove(httpd.json_file)


def test_http_proxy():
    httpd = services.HTTPCollector(port=8080)
    httpd.add_route('/collect/', ['GET'], httpd.collect)
    story = scenarios.Scenario(interval=0, http_proxy='http://127.0.0.1:8080')
    story.add_scene(HttpGetProxy)
    story.add_scene(Stop)
    story.add_service(httpd)
    story.play()
    with open(httpd.json_file, 'r') as fil:
        contents = fil.read()
        assert 'http_proxy' in contents
    os.remove(httpd.json_file)


def test_http_headers():
    httpd = services.HTTPCollector()
    httpd.add_route('/collect/', ['GET', 'POST'], httpd.collect)
    story = scenarios.Scenario(interval=0, http_headers={'User-Agent': 'Some Strange UA'})
    story.add_scene(HttpGet)
    story.add_scene(Stop)
    story.add_service(httpd)
    story.play()
    with open(httpd.json_file, 'r') as fil:
        contents = fil.read()
        assert '"user-agent": "Some Strange UA"' in contents
    os.remove(httpd.json_file)
