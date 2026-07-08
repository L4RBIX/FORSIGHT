"""
Plug your existing PyBullet risk simulation in here. This is the one function
the rest of the backend calls — Limelight ingestion, the WebSocket server, and
the scanning/predicting state machine are already wired to match FORESIGHT's
contract, so this is the only integration seam.

Replace the body of `run_simulation` with a call into your existing module, e.g.:

    from my_pybullet_sim import simulate_action  # your existing code

    def run_simulation(objects, action):
        result = simulate_action(objects, action)
        return Prediction(
            risk=result.fall_probability,
            verdict="BLOCK" if result.fall_probability >= 0.3 else ...,
            outcome=result.description,
            reason=result.summary,
            n_sims=result.num_rollouts,
            trajectories=result.rollout_paths,  # list[list[(x, y, z)]]
            safety_rule=SAFETY_RULE,
        )

The placeholder below is a rough heuristic (mirrors the frontend's
mock/customAction.ts) so the server runs end-to-end before your real sim is wired in.
"""
from __future__ import annotations

import random

from contract import ActionInfo, DetectedObject, Prediction

SAFETY_RULE = "Block if fall probability > 30%"
N_SIMS = 30


def run_simulation(objects: list[DetectedObject], action: ActionInfo) -> Prediction:
    """TODO: replace this body with a call into your PyBullet sim."""
    target = next((o for o in objects if o.id == action.object_id), None)
    near_edge = target.near_edge if target else False
    label = target.label if target else "object"

    text = action.text.lower()
    risk = 0.15 + random.random() * 0.25
    if any(w in text for w in ("edge", "off", "knock", "drop", "fall", "fast", "hard")):
        risk += 0.35
    if near_edge:
        risk += 0.2
    if any(w in text for w in ("gentle", "slow", "careful", "center")):
        risk -= 0.25
    risk = max(0.02, min(0.97, risk))

    verdict = "BLOCK" if risk >= 0.6 else "CAUTION" if risk >= 0.25 else "SAFE"
    fail_count = round(risk * N_SIMS)

    if verdict == "SAFE":
        outcome = f"{label} settles safely"
        reason = f"0 of {N_SIMS} simulations end with any object leaving the table"
    else:
        outcome = f"{label} may leave the table"
        reason = f"{fail_count} of {N_SIMS} simulations end with the {label} leaving the table"

    trajectories: list[list[tuple[float, float, float]]] = []
    if target:
        trajectories.append([target.pos, (target.pos[0] + 0.05, target.pos[1] + 0.05, 0.0)])

    return Prediction(
        risk=risk,
        verdict=verdict,  # type: ignore[arg-type]
        outcome=outcome,
        reason=reason,
        n_sims=N_SIMS,
        trajectories=trajectories,
        safety_rule=SAFETY_RULE,
    )
