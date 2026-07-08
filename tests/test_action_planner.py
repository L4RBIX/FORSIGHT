from foresight.parser.command_parser import parse_command
from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.planning.action_planner import plan_action


def scene():
    return FakePerceptionProvider().get_scene()


def test_push_blue_box_toward_mug():
    result = plan_action(parse_command("push the blue box toward the mug"), scene())
    assert result.ok
    assert result.skill.target_object_id == "obj_blue_box"
    assert result.skill.reference_object_id == "obj_mug"
    assert result.skill.direction_vector_world is not None


def test_push_box_right_multiple_boxes_clarifies():
    result = plan_action(parse_command("push box right"), scene())
    assert not result.ok
    assert result.status == "CLARIFICATION_NEEDED"


def test_mug_away_from_edge():
    result = plan_action(parse_command("push the mug away from edge"), scene())
    assert result.ok
    assert result.skill.direction_vector_world[0] < 0 or result.skill.direction_vector_world[1] < 0


def test_unknown_target_needs_grounding():
    result = plan_action(parse_command("push the green bottle right"), scene())
    assert result.status == "NEEDS_GROUNDING"
