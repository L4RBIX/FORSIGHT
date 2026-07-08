from foresight.robot.executor import DryRunExecutor
from foresight.schemas import RobotSkillRequest, SafetyDecision


def test_dry_run_blocks_unsafe():
    decision = SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason="no")
    skill = RobotSkillRequest(skill_type="push", target_object_id="obj", direction_vector_world=(1,0,0))
    assert not DryRunExecutor().execute(decision, skill).sent


def test_dry_run_sends_safe():
    decision = SafetyDecision(status="READY_FOR_EXECUTOR", allowed=True, reason="ok")
    skill = RobotSkillRequest(skill_type="push", target_object_id="obj", direction_vector_world=(1,0,0))
    assert DryRunExecutor().execute(decision, skill).sent
