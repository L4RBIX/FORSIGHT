from __future__ import annotations

import math
import random

from foresight.config import CONFIG, AppConfig
from foresight.schemas import Pose3D, RobotSkillRequest, SceneGraph, SimulationOutcome
from foresight.simulation.monte_carlo import sample_rollout, trajectory
from foresight.simulation.risk_metrics import collision_on_path, crosses_boundary, near_boundary_probability
from foresight.world.scene_graph import find_object


class ConsequenceOracle:
    """Monte Carlo consequence oracle.

    The implementation is intentionally robust without PyBullet: if pybullet is
    installed, teams can expand this class with full rigid-body rollouts; the
    included deterministic approximation already demonstrates uncertainty,
    boundary, and collision risk for the hackathon demo.
    """

    def __init__(self, config: AppConfig = CONFIG, fast_mode: bool = True, seed: int | None = None):
        self.config = config
        self.fast_mode = fast_mode
        self.seed = config.oracle_seed if seed is None else seed

    def predict(self, scene: SceneGraph, skill: RobotSkillRequest, n: int | None = None) -> SimulationOutcome:
        if skill.skill_type not in {"push", "point_at"}:
            return SimulationOutcome(
                fall_probability=0.0,
                collision_probability=0.0,
                boundary_risk_probability=0.0,
                verdict="SAFE",
                reason="No physical push consequence to simulate",
            )
        if not skill.target_object_id or not skill.direction_vector_world:
            return SimulationOutcome(
                fall_probability=1.0,
                collision_probability=0.0,
                boundary_risk_probability=1.0,
                verdict="UNSAFE",
                reason="Missing grounded target or direction vector",
            )

        target_original = find_object(scene, skill.target_object_id)
        if target_original is None:
            return SimulationOutcome(
                fall_probability=1.0,
                collision_probability=0.0,
                boundary_risk_probability=1.0,
                verdict="UNSAFE",
                reason="Target object disappeared before simulation",
            )

        n_rollouts = n or (self.config.oracle_fast_rollouts if self.fast_mode else self.config.oracle_rollouts)
        rng = random.Random(self.seed)
        dx, dy, dz = skill.direction_vector_world
        norm = math.sqrt(dx * dx + dy * dy + dz * dz)
        if norm < 1e-9:
            return SimulationOutcome(1.0, 0.0, 1.0, verdict="UNSAFE", reason="Zero direction vector")
        ux, uy = dx / norm, dy / norm
        falls = 0
        collisions = 0
        boundary_risks = 0
        boundary_risk_accumulator = 0.0
        target_traj: list[Pose3D] = []

        for i in range(n_rollouts):
            rollout = sample_rollout(scene, skill, rng)
            if rollout is None:
                falls += 1
                boundary_risks += 1
                continue
            target = rollout.target
            effective_distance = rng.gauss(skill.distance_m, scene.uncertainty.position_std_m * 2.0)
            final_x = target.pose.x + ux * max(0.0, effective_distance)
            final_y = target.pose.y + uy * max(0.0, effective_distance)
            bprob = near_boundary_probability(final_x, final_y, scene.workspace)

            # If a command moves toward a reference object that itself sits near the edge,
            # mark non-zero boundary risk even before the target reaches the edge. This is
            # a demo-oriented conservative model, not a claim of physical certainty.
            if skill.reference_object_id:
                ref = find_object(scene, skill.reference_object_id)
                if ref is not None:
                    ref_edge_risk = near_boundary_probability(ref.pose.x, ref.pose.y, scene.workspace, soft_margin_m=0.12)
                    if ref_edge_risk > 0:
                        bprob = max(bprob, 0.10 * ref_edge_risk)

            boundary_risk_accumulator += bprob
            if crosses_boundary(final_x, final_y, scene.workspace):
                falls += 1
                boundary_risks += 1
            elif bprob > rng.random():
                boundary_risks += 1

            if any(collision_on_path(target, other, final_x, final_y) for other in rollout.others):
                collisions += 1

            if i == 0:
                target_traj = trajectory(target.pose, final_x, final_y)

        fall_probability = falls / n_rollouts
        collision_probability = collisions / n_rollouts
        boundary_probability = max(boundary_risks / n_rollouts, min(1.0, boundary_risk_accumulator / n_rollouts))
        if fall_probability >= 0.50 or collision_probability >= 0.50:
            verdict = "UNSAFE"
        elif max(fall_probability, collision_probability, boundary_probability) >= 0.20:
            verdict = "RISKY"
        else:
            verdict = "SAFE"
        reason = (
            f"Monte Carlo approximation over {n_rollouts} rollouts: "
            f"fall={fall_probability:.2f}, collision={collision_probability:.2f}, boundary={boundary_probability:.2f}"
        )
        return SimulationOutcome(
            fall_probability=fall_probability,
            collision_probability=collision_probability,
            boundary_risk_probability=boundary_probability,
            trajectories={skill.target_object_id: target_traj},
            verdict=verdict,
            reason=reason,
        )
