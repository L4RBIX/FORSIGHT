from __future__ import annotations

from foresight.config import CONFIG, AppConfig
from foresight.schemas import RobotSkillRequest, SafetyDecision, SceneGraph, SimulationOutcome
from foresight.world.scene_graph import find_object


class SafetyGate:
    def __init__(self, config: AppConfig = CONFIG):
        self.config = config

    def decide(self, scene: SceneGraph, skill: RobotSkillRequest | None, outcome: SimulationOutcome | None = None) -> SafetyDecision:
        if skill is None:
            return SafetyDecision(status="NEEDS_GROUNDING", allowed=False, reason="No skill request was produced")

        if skill.skill_type == "scan_scene":
            return SafetyDecision(status="EXECUTABLE_SCAN_ONLY", allowed=True, reason="Scene scan is allowed without movement", outcome=outcome)
        if skill.skill_type == "stop":
            return SafetyDecision(status="READY_FOR_EXECUTOR", allowed=True, reason="Stop is allowed immediately", outcome=outcome)

        if not skill.target_object_id:
            return SafetyDecision(status="NEEDS_GROUNDING", allowed=False, reason="Physical action has no grounded target")
        target = find_object(scene, skill.target_object_id)
        if target is None:
            return SafetyDecision(status="NEEDS_GROUNDING", allowed=False, reason="Target object not present in scene")
        if not target.movable:
            return SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason=f"Target {target.label} is not movable")
        if target.class_name.lower() in self.config.forbidden_classes:
            return SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason=f"Forbidden target class: {target.class_name}")
        if skill.force_n > self.config.max_force_n:
            return SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason=f"Force {skill.force_n:.2f}N exceeds limit {self.config.max_force_n:.2f}N")
        if skill.distance_m > self.config.max_distance_m:
            return SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason=f"Distance {skill.distance_m:.2f}m exceeds limit {self.config.max_distance_m:.2f}m")
        if skill.simulation_required and outcome is None:
            return SafetyDecision(status="SIMULATION_REQUIRED", allowed=False, reason="Simulation outcome is required before execution")
        if outcome is None:
            return SafetyDecision(status="SIMULATION_REQUIRED", allowed=False, reason="Missing simulation outcome")
        if outcome.fall_probability > self.config.max_fall_prob:
            return SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason="Fall probability is too high", outcome=outcome)
        if outcome.collision_probability > self.config.max_collision_prob:
            return SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason="Collision probability is too high", outcome=outcome)
        if outcome.boundary_risk_probability > self.config.max_boundary_prob:
            return SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason="Boundary risk is too high", outcome=outcome)
        if outcome.verdict == "UNSAFE":
            return SafetyDecision(status="REJECTED_UNSAFE", allowed=False, reason="Simulation verdict is UNSAFE", outcome=outcome)
        return SafetyDecision(status="READY_FOR_EXECUTOR", allowed=True, reason="Simulation and policy checks passed", outcome=outcome)
