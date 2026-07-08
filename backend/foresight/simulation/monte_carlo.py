from __future__ import annotations

import random
from dataclasses import dataclass

from foresight.schemas import ObjectState, Pose3D, RobotSkillRequest, SceneGraph
from foresight.world.uncertainty import sample_pose


@dataclass(frozen=True)
class RolloutState:
    target: ObjectState
    others: list[ObjectState]


def sample_rollout(scene: SceneGraph, skill: RobotSkillRequest, rng: random.Random) -> RolloutState | None:
    if not skill.target_object_id:
        return None
    sampled: list[ObjectState] = []
    for obj in scene.objects:
        pose = sample_pose(obj.pose, scene.uncertainty, rng)
        sampled.append(obj.model_copy(update={"pose": pose}))
    target = next((o for o in sampled if o.id == skill.target_object_id), None)
    if target is None:
        return None
    return RolloutState(target=target, others=[o for o in sampled if o.id != target.id])


def trajectory(start: Pose3D, final_x: float, final_y: float, steps: int = 8) -> list[Pose3D]:
    out = []
    for i in range(steps + 1):
        t = i / steps
        out.append(Pose3D(x=start.x + (final_x - start.x) * t, y=start.y + (final_y - start.y) * t, z=start.z, yaw=start.yaw))
    return out
