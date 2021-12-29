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

    async def task(self, url, headers):
        response = await self.http_get(url, headers)
        logging.debug('Got HTTP response: ' + str(response))
        if response['status'] == 200:
            self.context['status_200'].append(url)
        if response['status'] == 404:
            self.context['status_404'].append(url)


class SendRequests(scenarios.Scene):

    async def task(self):
        target_404 = f'http://127.0.0.1:8888/not_found'
        self.queue.add(HttpGet, target_404, headers=self.context['headers'])
        for idx in range(10):
            target = f'http://127.0.0.1:8888/collect?task_no={idx}'
            self.queue.add(HttpGet, target, headers=self.context['headers'])


def test_queues():
    context = {
        'status_200': list(),
        'status_404': list(),
        'headers': {'User-Agent': 'dummy'},
    }
    httpd = services.HTTPCollector()
    httpd.add_route('/collect/', ['GET'], httpd.collect)
    story = scenarios.Scenario(interval=0, context=context)
    story.add_scene(SendRequests)
    story.add_scene(Stop)
    story.add_service(httpd)
    story.play()
    assert len(context['status_200']) == 10
    assert len(context['status_404']) == 1
    os.remove(httpd.json_file)
