import os
import tempfile

from sanic import Sanic
import pytest

from horrors import (
    logging,
    scenarios,
    services,
)


Sanic.test_mode = True


class Stop(scenarios.Scene):

    async def task(self):
        self.scenario.stop()


class HttpGet(scenarios.Scene):

    def touch_tmp(self):
        logging.info('Writing to `' + self.context['temp_file'].name + '`')
        with self.context['temp_file'] as fil:
            fil.write(b'Temporary')

    def sleep_a_bit(self):
        os.system('sleep 10')

    async def task(self):
        self.thread_exec(self.sleep_a_bit)
        self.thread_exec(self.touch_tmp)
        await self.http_get(
            'http://127.0.0.1:8888/collect/?test=http_background'
        )


def test_http_thread_exec():
    context = {
        'temp_file': tempfile.NamedTemporaryFile(delete=False)
    }
    httpd = services.HTTPCollector()
    httpd.add_route('/collect/', ['GET', 'POST'], httpd.collect)
    story = scenarios.Scenario(interval=0, context=context)
    story.add_scene(HttpGet)
    story.add_scene(Stop)
    story.add_service(httpd)
    story.play()

    with open(httpd.json_file, 'r') as fil:
        contents = fil.read()
        assert 'http_background' in contents
    os.remove(httpd.json_file)

    temp_path = context['temp_file'].name
    with open(temp_path, 'r') as fil:
        contents = fil.read()
        assert 'Temporary' in contents
    os.remove(temp_path)

