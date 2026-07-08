from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.simulation.pybullet_twin import PyBulletTwin


def test_pybullet_twin_direct_no_crash_even_if_missing():
    twin = PyBulletTwin(gui=False)
    scene = FakePerceptionProvider().get_scene()
    twin.load_scene(scene)
    twin.update_scene(scene)
    state = twin.snapshot()
    twin.restore(state)
    twin.disconnect()
