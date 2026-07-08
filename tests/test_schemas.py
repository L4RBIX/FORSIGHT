from foresight.schemas import ObjectState, ParsedCommand, Pose3D, SpatialGoal


def test_object_state_alias_class():
    obj = ObjectState(
        id="x",
        label="blue box",
        **{"class": "box"},
        pose=Pose3D(x=0, y=0, z=0),
        size_m=(0.1, 0.1, 0.1),
        confidence=0.9,
        source="fake",
    )
    assert obj.class_name == "box"
    assert obj.model_dump(by_alias=True)["class"] == "box"


def test_parsed_command_defaults():
    cmd = ParsedCommand(raw_command="scan", action="scan_scene")
    assert cmd.spatial_goal.type == "none"
    assert cmd.confidence == 1.0
