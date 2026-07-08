from foresight.parser.command_parser import parse_command
from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.planning.action_planner import plan_action
from foresight.simulation.oracle import ConsequenceOracle


def _outcome(command):
    scene = FakePerceptionProvider().get_scene()
    skill = plan_action(parse_command(command), scene).skill
    return ConsequenceOracle(fast_mode=True, seed=123).predict(scene, skill, n=20)


def test_toward_mug_near_edge_has_nonzero_risk():
    outcome = _outcome("push the blue box toward the mug")
    assert outcome.boundary_risk_probability > 0.0


def test_away_from_edge_lower_risk_than_toward_edge():
    toward = _outcome("push the mug right 20 cm")
    away = _outcome("push the mug away from edge")
    assert away.boundary_risk_probability <= toward.boundary_risk_probability
