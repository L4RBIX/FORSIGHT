from __future__ import annotations

import math

from foresight.schemas import ParsedCommand, PlanningResult, ReferenceSelector, RobotSkillRequest, SceneGraph, TargetSelector
from foresight.world.scene_graph import find_object, match_selector

DIRECTION_VECTORS: dict[str, tuple[float, float, float]] = {
    "right": (1.0, 0.0, 0.0),
    "left": (-1.0, 0.0, 0.0),
    "forward": (0.0, 1.0, 0.0),
    "back": (0.0, -1.0, 0.0),
}


def _normalize(x: float, y: float) -> tuple[float, float, float] | None:
    norm = math.hypot(x, y)
    if norm < 1e-9:
        return None
    return (x / norm, y / norm, 0.0)


def _selector_from_reference(ref: ReferenceSelector) -> TargetSelector:
    return TargetSelector(object_id=ref.object_id, class_name=ref.class_name)


def _ground_reference(parsed: ParsedCommand, scene: SceneGraph, target_id: str) -> tuple[str | None, tuple[float, float, float] | None, str | None]:
    ref = parsed.reference
    if not ref:
        return None, None, "Missing reference object"

    if ref.relation == "edge":
        target = find_object(scene, target_id)
        if target is None:
            return None, None, "Target disappeared"
        distances = {
            "x_min": target.pose.x - scene.workspace.x_min,
            "x_max": scene.workspace.x_max - target.pose.x,
            "y_min": target.pose.y - scene.workspace.y_min,
            "y_max": scene.workspace.y_max - target.pose.y,
        }
        edge = min(distances, key=distances.get)
        vector = {
            "x_min": (1.0, 0.0, 0.0),
            "x_max": (-1.0, 0.0, 0.0),
            "y_min": (0.0, 1.0, 0.0),
            "y_max": (0.0, -1.0, 0.0),
        }[edge]
        return None, vector, None

    candidates = match_selector(scene, _selector_from_reference(ref))
    candidates = [obj for obj in candidates if obj.id != target_id]
    if not candidates:
        return None, None, "Reference object not found"
    if len(candidates) > 1:
        labels = ", ".join(obj.label for obj in candidates)
        return None, None, f"Reference is ambiguous: {labels}"

    reference = candidates[0]
    target = find_object(scene, target_id)
    if target is None:
        return None, None, "Target disappeared"
    if parsed.spatial_goal.type == "away_from_reference":
        vec = _normalize(target.pose.x - reference.pose.x, target.pose.y - reference.pose.y)
    else:
        vec = _normalize(reference.pose.x - target.pose.x, reference.pose.y - target.pose.y)
    if vec is None:
        return reference.id, None, "Target and reference are at the same position"
    return reference.id, vec, None


def plan_action(parsed: ParsedCommand, scene: SceneGraph) -> PlanningResult:
    if parsed.action == "scan_scene":
        return PlanningResult(
            ok=True,
            status="PLANNED",
            reason="Scan scene does not require physical movement",
            skill=RobotSkillRequest(skill_type="scan_scene", simulation_required=False),
        )
    if parsed.action == "stop":
        return PlanningResult(
            ok=True,
            status="PLANNED",
            reason="Stop command is always safe to send as a high-level skill",
            skill=RobotSkillRequest(skill_type="stop", simulation_required=False),
        )
    if parsed.action != "push":
        return PlanningResult(ok=False, status="REJECTED", reason=f"Unsupported action: {parsed.action}")
    if parsed.confidence < 0.5:
        return PlanningResult(ok=False, status="CLARIFICATION_NEEDED", reason="Parser confidence is too low", clarification_question="What exactly should the robot move?")

    candidates = match_selector(scene, parsed.target)
    if not candidates:
        return PlanningResult(ok=False, status="NEEDS_GROUNDING", reason="No scene object matches the target selector")
    if len(candidates) > 1:
        labels = ", ".join(obj.label for obj in candidates)
        return PlanningResult(
            ok=False,
            status="CLARIFICATION_NEEDED",
            reason="Multiple objects match the target selector",
            clarification_question=f"Which object do you mean: {labels}?",
        )
    target = candidates[0]

    vector: tuple[float, float, float] | None = None
    reference_id: str | None = None
    if parsed.spatial_goal.type == "direction":
        if not parsed.spatial_goal.direction:
            return PlanningResult(ok=False, status="NEEDS_GROUNDING", reason="Missing movement direction")
        vector = DIRECTION_VECTORS[parsed.spatial_goal.direction]
    elif parsed.spatial_goal.type in {"toward_reference", "away_from_reference"}:
        reference_id, vector, err = _ground_reference(parsed, scene, target.id)
        if err:
            status = "CLARIFICATION_NEEDED" if "ambiguous" in err.lower() else "NEEDS_GROUNDING"
            return PlanningResult(ok=False, status=status, reason=err, clarification_question=err if status == "CLARIFICATION_NEEDED" else None)
    else:
        return PlanningResult(ok=False, status="NEEDS_GROUNDING", reason="No spatial goal was parsed")

    if vector is None:
        return PlanningResult(ok=False, status="NEEDS_GROUNDING", reason="Could not compute a movement vector")

    return PlanningResult(
        ok=True,
        status="PLANNED",
        reason=f"Planned {parsed.action} for {target.label}",
        skill=RobotSkillRequest(
            skill_type=parsed.action,
            target_object_id=target.id,
            reference_object_id=reference_id,
            direction_vector_world=vector,
            distance_m=parsed.spatial_goal.distance_m,
            force_n=4.0,
            simulation_required=True,
        ),
    )
