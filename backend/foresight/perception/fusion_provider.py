"""Perception provider that fuses AprilTag, YOLO, and LocateAnything signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from foresight.config import CONFIG, AppConfig
from foresight.perception.base import PerceptionProvider
from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.perception.frame_source import FakeFrameSource, FrameSource
from foresight.perception.fusion import SceneFusion
from foresight.perception.yolo_tracker import YoloTracker
from foresight.schemas import Detection2D, SceneGraph


@dataclass
class FusionPerceptionProvider:
    apriltag_provider: PerceptionProvider | None = None
    frame_source: FrameSource | None = None
    yolo_tracker: YoloTracker | None = None
    fusion: SceneFusion = field(default_factory=SceneFusion)
    config: AppConfig = field(default_factory=lambda: CONFIG)
    fallback_provider: PerceptionProvider = field(default_factory=FakePerceptionProvider)
    use_fake_when_empty: bool = True

    def __post_init__(self) -> None:
        if self.frame_source is None:
            self.frame_source = FakeFrameSource()
        if self.yolo_tracker is None:
            self.yolo_tracker = YoloTracker(self.config)
        self._latest_locate_detections: list[Detection2D] = []
        self._last_warnings: list[str] = []

    @property
    def latest_locate_detections(self) -> list[Detection2D]:
        return list(self._latest_locate_detections)

    def set_locate_detections(self, detections: list[Detection2D]) -> None:
        self._latest_locate_detections = list(detections)

    def clear_locate_detections(self) -> None:
        self._latest_locate_detections = []

    def get_scene(self) -> SceneGraph:
        warnings: list[str] = []
        apriltag_scene: SceneGraph | None = None
        if self.apriltag_provider is not None:
            try:
                apriltag_scene = self.apriltag_provider.get_scene()
                warnings.extend(apriltag_scene.warnings)
            except Exception as exc:
                warnings.append(f"AprilTag/Limelight source failed: {exc}")

        frame: Any | None = None
        if self.frame_source is not None:
            try:
                packet = self.frame_source.read_frame()
                frame = packet.frame
                warnings.extend(packet.warnings)
            except Exception as exc:
                warnings.append(f"Frame source failed: {exc}")

        yolo_detections: list[Detection2D] = []
        if frame is not None and self.yolo_tracker is not None:
            try:
                yolo_detections = self.yolo_tracker.track_frame(frame)
            except Exception as exc:
                warnings.append(f"YOLO tracker failed: {exc}")

        try:
            scene = self.fusion.fuse(apriltag_scene, yolo_detections, self._latest_locate_detections)
        except Exception as exc:
            warnings.append(f"Scene fusion failed: {exc}")
            scene = apriltag_scene or self.fallback_provider.get_scene()

        scene.warnings.extend(w for w in warnings if w not in scene.warnings)
        if self.use_fake_when_empty and not scene.objects and apriltag_scene is None and not yolo_detections and not self._latest_locate_detections:
            fallback = self.fallback_provider.get_scene()
            fallback.warnings.extend(scene.warnings)
            fallback.warnings.append("Fusion provider had no usable sources; using fake fallback scene")
            scene = fallback
        self._last_warnings = list(scene.warnings)
        return scene
