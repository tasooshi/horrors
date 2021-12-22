import pytest

from horrors import scenarios


HTTP_PROXY = 'http://127.0.0.1:8080'
ATTACKER_HOST = '127.0.0.1'
ATTACKER_PORT = 8000
TARGET_HOST = '127.0.0.1'
TARGET_PORT = 8888


def test_scene_context():

    class TestScene(scenarios.Scene):

        async def task(self):
            assert self.context['ahost'] == ATTACKER_HOST
            assert self.context['aport'] == ATTACKER_PORT
            assert self.context['thost'] == TARGET_HOST
            assert self.context['tport'] == TARGET_PORT

    context = {
        'ahost': ATTACKER_HOST,
        'aport': ATTACKER_PORT,
        'thost': TARGET_HOST,
        'tport': TARGET_PORT,
    }
    story = scenarios.Scenario(keep_running=False, **context)
    story.add_scene(TestScene)
    story.set_debug()
    story.play()


def test_scene_order():
    pass


def test_scene_execution():
    pass
