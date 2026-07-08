"""
Mirrors src/types/telemetry.ts field-for-field. This is the wire contract —
both sides (this backend and the dashboard) must agree on it exactly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Verdict = Literal["SAFE", "CAUTION", "BLOCK"]
Mode = Literal["live", "scanning", "predicting"]
Vec3 = tuple[float, float, float]
BBox = tuple[float, float, float, float]  # normalized [x, y, w, h], 0-1


@dataclass
class DetectedObject:
    id: str
    label: str
    confidence: float
    pos: Vec3
    size: Vec3
    movable: bool
    near_edge: bool
    bbox: BBox

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "confidence": self.confidence,
            "pos": list(self.pos),
            "size": list(self.size),
            "movable": self.movable,
            "near_edge": self.near_edge,
            "bbox": list(self.bbox),
        }


@dataclass
class SensorInfo:
    pos_noise_mm: float
    rot_noise_deg: float
    tracking: Literal["ok", "degraded", "lost"] = "ok"

    def to_dict(self) -> dict:
        return {
            "pos_noise_mm": self.pos_noise_mm,
            "rot_noise_deg": self.rot_noise_deg,
            "tracking": self.tracking,
        }


@dataclass
class ActionInfo:
    text: str
    object_id: Optional[str]
    dir: Vec3
    force_n: float

    def to_dict(self) -> dict:
        return {"text": self.text, "object_id": self.object_id, "dir": list(self.dir), "force_n": self.force_n}


@dataclass
class Prediction:
    risk: float
    verdict: Verdict
    outcome: str
    reason: str
    n_sims: int
    trajectories: list[list[Vec3]]
    safety_rule: str

    def to_dict(self) -> dict:
        return {
            "risk": self.risk,
            "verdict": self.verdict,
            "outcome": self.outcome,
            "reason": self.reason,
            "n_sims": self.n_sims,
            "trajectories": [[list(p) for p in traj] for traj in self.trajectories],
            "safety_rule": self.safety_rule,
        }


@dataclass
class TelemetryFrame:
    timestamp: float
    mode: Mode
    camera_frame: Optional[str]
    objects: list[DetectedObject]
    sensor: SensorInfo
    action: Optional[ActionInfo]
    prediction: Optional[Prediction]

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "mode": self.mode,
            "camera_frame": self.camera_frame,
            "objects": [o.to_dict() for o in self.objects],
            "sensor": self.sensor.to_dict(),
            "action": self.action.to_dict() if self.action else None,
            "prediction": self.prediction.to_dict() if self.prediction else None,
        }
