"""Typed schemas for all module boundaries.

Pydantic v2 models are used wherever data crosses module boundaries. The parser
produces intent only; physical simulation and safety decide executability.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Pose3D(BaseModel):
    x: float
    y: float
    z: float
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    def xy(self) -> tuple[float, float]:
        return (self.x, self.y)


class ObjectState(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    label: str
    class_name: str = Field(alias="class")
    color: str | None = None
    pose: Pose3D
    size_m: tuple[float, float, float]
    mass_kg: float = 0.1
    movable: bool = True
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["fake", "limelight", "yolo", "locateanything", "fused"]
    tag_id: int | None = None
    velocity_mps: tuple[float, float, float] | None = None


class SensorUncertainty(BaseModel):
    position_std_m: float = 0.005
    rotation_std_deg: float = 2.0


class WorkspaceBounds(BaseModel):
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float = 0.0
    z_max: float = 1.0

    def contains_xy(self, x: float, y: float, margin_m: float = 0.0) -> bool:
        return (
            self.x_min + margin_m <= x <= self.x_max - margin_m
            and self.y_min + margin_m <= y <= self.y_max - margin_m
        )

    def min_distance_to_edge(self, x: float, y: float) -> float:
        return min(x - self.x_min, self.x_max - x, y - self.y_min, self.y_max - y)


class SceneGraph(BaseModel):
    timestamp_s: float
    world_frame: str = "table_anchor"
    objects: list[ObjectState]
    workspace: WorkspaceBounds
    uncertainty: SensorUncertainty
    warnings: list[str] = Field(default_factory=list)


ActionType = Literal["scan_scene", "push", "point_at", "stop"]


class TargetSelector(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object_id: str | None = None
    class_name: str | None = Field(default=None, alias="class")
    color: str | None = None
    label_contains: str | None = None


class ReferenceSelector(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object_id: str | None = None
    class_name: str | None = Field(default=None, alias="class")
    relation: Literal["toward", "away_from", "near", "edge"] | None = None


class SpatialGoal(BaseModel):
    type: Literal["direction", "toward_reference", "away_from_reference", "none"]
    direction: Literal["left", "right", "forward", "back"] | None = None
    frame: Literal["table", "camera", "robot_base"] = "table"
    distance_m: float = Field(default=0.10, ge=0.0, le=0.50)


class ParsedCommand(BaseModel):
    raw_command: str
    action: ActionType
    target: TargetSelector | None = None
    reference: ReferenceSelector | None = None
    spatial_goal: SpatialGoal = Field(default_factory=lambda: SpatialGoal(type="none"))
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    needs_grounding: bool = True


class RobotSkillRequest(BaseModel):
    skill_type: ActionType
    target_object_id: str | None = None
    reference_object_id: str | None = None
    direction_vector_world: tuple[float, float, float] | None = None
    distance_m: float = 0.10
    force_n: float = 4.0
    simulation_required: bool = True


class SimulationOutcome(BaseModel):
    fall_probability: float = Field(ge=0.0, le=1.0)
    collision_probability: float = Field(ge=0.0, le=1.0)
    boundary_risk_probability: float = Field(ge=0.0, le=1.0)
    trajectories: dict[str, list[Pose3D]] = Field(default_factory=dict)
    verdict: Literal["SAFE", "RISKY", "UNSAFE"]
    reason: str


class SafetyDecision(BaseModel):
    status: Literal[
        "EXECUTABLE_SCAN_ONLY",
        "NEEDS_GROUNDING",
        "SIMULATION_REQUIRED",
        "READY_FOR_EXECUTOR",
        "CLARIFICATION_NEEDED",
        "REJECTED_UNSAFE",
    ]
    allowed: bool
    reason: str
    outcome: SimulationOutcome | None = None


class Detection2D(BaseModel):
    label: str
    class_name: str = Field(alias="class")
    bbox_xyxy: tuple[float, float, float, float] | None = None
    point_xy: tuple[float, float] | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: Literal["yolo", "locateanything"]
    track_id: int | None = None
    color: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class LocateAnythingResult(BaseModel):
    ok: bool
    query: str
    detections: list[Detection2D] = Field(default_factory=list)
    error: str | None = None
    raw: object | None = None


class PlanningResult(BaseModel):
    ok: bool
    skill: RobotSkillRequest | None = None
    status: Literal["PLANNED", "NEEDS_GROUNDING", "CLARIFICATION_NEEDED", "REJECTED"]
    reason: str
    clarification_question: str | None = None


class RobotExecutionResult(BaseModel):
    sent: bool
    reason: str
    executor: str = "dry_run"
    response: object | None = None


class FullPipelineResult(BaseModel):
    command: str
    scene: SceneGraph
    parsed: ParsedCommand
    planning: PlanningResult
    simulation: SimulationOutcome | None
    safety: SafetyDecision
    robot_skill: RobotSkillRequest | None
