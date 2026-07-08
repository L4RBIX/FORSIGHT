from __future__ import annotations

import math
from collections.abc import Iterable

from foresight.schemas import ObjectState, SceneGraph, TargetSelector


def object_radius_xy(obj: ObjectState) -> float:
    return 0.5 * math.hypot(obj.size_m[0], obj.size_m[1])


def find_object(scene: SceneGraph, object_id: str) -> ObjectState | None:
    return next((obj for obj in scene.objects if obj.id == object_id), None)


def match_selector(scene: SceneGraph, selector: TargetSelector | None) -> list[ObjectState]:
    if selector is None:
        return []
    candidates: Iterable[ObjectState] = scene.objects
    if selector.object_id:
        candidates = [o for o in candidates if o.id == selector.object_id]
    if selector.class_name:
        candidates = [o for o in candidates if o.class_name == selector.class_name]
    if selector.color:
        candidates = [o for o in candidates if (o.color or "").lower() == selector.color.lower()]
    if selector.label_contains:
        needle = selector.label_contains.lower()
        candidates = [o for o in candidates if needle in o.label.lower()]
    return list(candidates)


def distance_xy(a: ObjectState, b: ObjectState) -> float:
    return math.hypot(a.pose.x - b.pose.x, a.pose.y - b.pose.y)
