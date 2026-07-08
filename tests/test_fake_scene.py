from foresight.perception.fake_perception import FakePerceptionProvider


def test_fake_scene_contains_expected_objects():
    scene = FakePerceptionProvider().get_scene()
    labels = {obj.label for obj in scene.objects}
    assert "blue box" in labels
    assert "red box" in labels
    assert any("mug" in label for label in labels)
    assert scene.workspace.x_min < 0 < scene.workspace.x_max
