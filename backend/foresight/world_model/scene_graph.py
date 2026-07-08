from typing import Literal

from pydantic import BaseModel, Field


class Uncertainty(BaseModel):
    position_mm: float = 4.0
    rotation_deg: float = 1.8


class SceneObject(BaseModel):
    id: str
    label: str
    object_class: str
    position: list[float]
    size: list[float]
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "mock"
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)


class SceneGraph(BaseModel):
    timestamp: float
    frame_id: str = "table"
    objects: list[SceneObject]
    mode: Literal["mock", "live"] = "mock"
