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
    story = scenarios.Scenario(keep_running=False, context=context)
    story.add_scene(TestScene)
    story.play()


def test_scene_order():

    class TestScene(scenarios.Scene):

        async def task(self):
            self.context['order'].append(self.when)

    context = {
        'order': list(),
    }
    story = scenarios.Scenario(keep_running=False, context=context)
    story.add_scene(TestScene)
    story.add_scene(TestScene)
    story.add_scene(TestScene)
    story.add_scene(TestScene)
    story.play()
    assert context['order'] == [1, 2, 3, 4]


def test_scene_order_states():

    class TestScene(scenarios.Scene):

        async def task(self):
            self.context['order'].append(self.when)

    class TestSceneOne(TestScene):

        next_event = 'two'

    class TestSceneTwo(TestScene):

        next_event = 'three'

    class TestSceneThree(TestScene):

        next_event = 'four'

    context = {
        'order': list(),
    }
    story = scenarios.Scenario(keep_running=False, context=context)
    story.add_scene(TestSceneOne)
    story.add_scene(TestSceneTwo, when='two')
    story.add_scene(TestSceneThree, when='three')
    story.add_scene(TestScene, when='four')
    story.play()
    assert context['order'] == [1, 'two', 'three', 'four']


def test_scenario_stop():

    class TestScene(scenarios.Scene):

        async def task(self):
            self.context['finished'].append(self.when)
            if self.when == 3:
                self.scenario.stop()

    context = {
        'finished': list(),
    }
    story = scenarios.Scenario(keep_running=False, context=context)
    story.add_scene(TestScene)
    story.add_scene(TestScene)
    story.add_scene(TestScene)
    story.add_scene(TestScene)
    story.play()
    assert context['finished'] == [1, 2, 3]
