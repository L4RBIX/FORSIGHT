from __future__ import annotations

import math

from foresight.schemas import ObjectState, WorkspaceBounds


def point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def crosses_boundary(x: float, y: float, workspace: WorkspaceBounds) -> bool:
    return not workspace.contains_xy(x, y, margin_m=0.0)


def near_boundary_probability(x: float, y: float, workspace: WorkspaceBounds, soft_margin_m: float = 0.06) -> float:
    d = workspace.min_distance_to_edge(x, y)
    if d < 0:
        return 1.0
    if d >= soft_margin_m:
        return 0.0
    return max(0.0, min(1.0, 1.0 - d / soft_margin_m))


def collision_on_path(target: ObjectState, other: ObjectState, final_x: float, final_y: float) -> bool:
    radius = 0.55 * math.hypot(target.size_m[0] + other.size_m[0], target.size_m[1] + other.size_m[1])
    return point_segment_distance(other.pose.x, other.pose.y, target.pose.x, target.pose.y, final_x, final_y) < radius
