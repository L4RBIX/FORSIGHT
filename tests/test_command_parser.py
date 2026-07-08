import pytest

from foresight.parser.command_parser import parse_command


@pytest.mark.parametrize(
    "text,action",
    [
        ("scan scene", "scan_scene"),
        ("сканируй сцену", "scan_scene"),
        ("stop", "stop"),
        ("остановись", "stop"),
        ("тоқта", "stop"),
    ],
)
def test_scan_stop(text, action):
    assert parse_command(text).action == action


@pytest.mark.parametrize(
    "text,color,cls,direction",
    [
        ("push the blue box right", "blue", "box", "right"),
        ("move the red cube left 10 cm", "red", "box", "left"),
        ("толкни синюю коробку вправо", "blue", "box", "right"),
        ("көк қорапты оңға жылжыт", "blue", "box", "right"),
        ("push the green bottle back", "green", "bottle", "back"),
        ("сдвинь красный куб налево", "red", "box", "left"),
    ],
)
def test_direction_commands(text, color, cls, direction):
    cmd = parse_command(text)
    assert cmd.action == "push"
    assert cmd.target.color == color
    assert cmd.target.class_name == cls
    assert cmd.spatial_goal.direction == direction


@pytest.mark.parametrize(
    "text,ref_cls,goal",
    [
        ("push the blue box toward the mug", "mug", "toward_reference"),
        ("подвинь красную коробку к кружке", "mug", "toward_reference"),
        ("қызыл кубты кружкаға қарай итер", "mug", "toward_reference"),
        ("push the mug away from edge", None, "away_from_reference"),
        ("move cup away from edge", None, "away_from_reference"),
    ],
)
def test_reference_commands(text, ref_cls, goal):
    cmd = parse_command(text)
    assert cmd.spatial_goal.type == goal
    assert cmd.reference is not None
    if ref_cls:
        assert cmd.reference.class_name == ref_cls
    else:
        assert cmd.reference.relation == "edge"


def test_distance_parsing_cm():
    assert parse_command("move the red cube left 10 cm").spatial_goal.distance_m == pytest.approx(0.10)
    assert parse_command("move the red cube left 25 см").spatial_goal.distance_m == pytest.approx(0.25)


def test_ambiguous_target_only_class():
    cmd = parse_command("push box right")
    assert cmd.target.class_name == "box"
    assert cmd.target.color is None


def test_invalid_command_low_confidence():
    cmd = parse_command("sing a song")
    assert cmd.action == "stop"
    assert cmd.confidence < 0.1


def test_dangerous_target_low_confidence():
    cmd = parse_command("push the human right")
    assert cmd.confidence < 0.5
