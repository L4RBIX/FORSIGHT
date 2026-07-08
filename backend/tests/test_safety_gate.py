from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.safety.safety_gate import SafetyGate
from foresight.schemas import RobotSkillRequest, SimulationOutcome


def test_scan_allowed_without_sim():
    scene = FakePerceptionProvider().get_scene()
    decision = SafetyGate().decide(scene, RobotSkillRequest(skill_type="scan_scene", simulation_required=False))
    assert decision.allowed
    assert decision.status == "EXECUTABLE_SCAN_ONLY"


def test_missing_sim_blocked():
    scene = FakePerceptionProvider().get_scene()
    skill = RobotSkillRequest(skill_type="push", target_object_id="obj_blue_box", direction_vector_world=(1, 0, 0))
    decision = SafetyGate().decide(scene, skill, None)
    assert decision.status == "SIMULATION_REQUIRED"


def test_safe_ready():
    scene = FakePerceptionProvider().get_scene()
    skill = RobotSkillRequest(skill_type="push", target_object_id="obj_blue_box", direction_vector_world=(1, 0, 0))
    outcome = SimulationOutcome(fall_probability=0, collision_probability=0, boundary_risk_probability=0, verdict="SAFE", reason="ok")
    decision = SafetyGate().decide(scene, skill, outcome)
    assert decision.allowed
    assert decision.status == "READY_FOR_EXECUTOR"


def test_unsafe_blocked():
    scene = FakePerceptionProvider().get_scene()
    skill = RobotSkillRequest(skill_type="push", target_object_id="obj_blue_box", direction_vector_world=(1, 0, 0))
    outcome = SimulationOutcome(fall_probability=0.9, collision_probability=0, boundary_risk_probability=0, verdict="UNSAFE", reason="fall")
    decision = SafetyGate().decide(scene, skill, outcome)
    assert not decision.allowed
    assert decision.status == "REJECTED_UNSAFE"


def test_force_limit_blocks():
    scene = FakePerceptionProvider().get_scene()
    skill = RobotSkillRequest(skill_type="push", target_object_id="obj_blue_box", direction_vector_world=(1, 0, 0), force_n=99)
    outcome = SimulationOutcome(fall_probability=0, collision_probability=0, boundary_risk_probability=0, verdict="SAFE", reason="ok")
    assert not SafetyGate().decide(scene, skill, outcome).allowed
