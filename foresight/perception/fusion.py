from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass, field

from foresight.geometry.homography import HomographyProjector
from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.schemas import Detection2D, ObjectState, Pose3D, SceneGraph, SensorUncertainty, WorkspaceBounds


@dataclass
class SceneFusion:
    homography: HomographyProjector | None = None
    history: dict[str, tuple[float, Pose3D]] = field(default_factory=dict)
    workspace: WorkspaceBounds = field(default_factory=lambda: WorkspaceBounds(x_min=-0.45, x_max=0.45, y_min=-0.30, y_max=0.30, z_min=0.0, z_max=0.60))
    nearest_dedupe_distance_m: float = 0.06

    @staticmethod
    def _slug(value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_") or "object"

    @staticmethod
    def _label_color(label: str) -> str | None:
        label_lower = label.lower()
        for color in ("blue", "red", "green", "yellow", "white", "black", "orange", "purple"):
            if color in label_lower:
                return color
        return None

    def _project(self, det: Detection2D) -> tuple[float, float, float, bool]:
        point = det.point_xy
        if point is None and det.bbox_xyxy is not None:
            x1, y1, x2, y2 = det.bbox_xyxy
            point = ((x1 + x2) / 2, y2)  # bottom-center for table contact
        if point is None:
            return (0.0, 0.0, 0.02, False)
        if self.homography:
            x, y = self.homography.image_point_to_table_xy(point)
            return (x, y, 0.02, True)
        # Low confidence approximate projection when uncalibrated.
        x = (float(point[0]) - 320.0) / 700.0
        y = (240.0 - float(point[1])) / 700.0
        return (
            max(self.workspace.x_min, min(self.workspace.x_max, x)),
            max(self.workspace.y_min, min(self.workspace.y_max, y)),
            0.02,
            False,
        )

    def _object_id(self, det: Detection2D, pose: Pose3D, index: int) -> str:
        if det.track_id is not None:
            return f"det_{det.source}_track_{det.track_id}"
        label = self._slug(det.label or det.class_name)
        # Quantized pose keeps IDs stable across small jitter while avoiding class/color collapse.
        qx = int(round(pose.x * 100))
        qy = int(round(pose.y * 100))
        return f"det_{det.source}_{label}_{qx}_{qy}_{index}"

    def _det_to_obj(self, det: Detection2D, source_weight: float, index: int) -> ObjectState:
        x, y, z, calibrated = self._project(det)
        class_name = det.class_name
        size = (0.07, 0.07, 0.08) if class_name in {"cup", "mug", "bottle"} else (0.08, 0.08, 0.08)
        pose = Pose3D(x=x, y=y, z=z)
        object_id = self._object_id(det, pose, index)
        now = time.time()
        velocity = None
        if object_id in self.history:
            prev_t, prev_pose = self.history[object_id]
            dt = max(1e-6, now - prev_t)
            velocity = ((pose.x - prev_pose.x) / dt, (pose.y - prev_pose.y) / dt, (pose.z - prev_pose.z) / dt)
        self.history[object_id] = (now, pose)
        confidence = det.confidence * source_weight
        if not calibrated:
            confidence *= 0.65
        return ObjectState(
            id=object_id,
            label=det.label,
            class_name=class_name,
            color=det.color or self._label_color(det.label),
            pose=pose,
            size_m=size,
            mass_kg=0.1,
            movable=True,
            confidence=min(0.95, max(0.05, confidence)),
            source="fused",
            velocity_mps=velocity,
        )

    @staticmethod
    def _distance_xy(a: Pose3D, b: Pose3D) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    @staticmethod
    def _same_semantic(a: ObjectState, b: ObjectState) -> bool:
        if a.class_name != b.class_name:
            return False
        if a.color is not None and b.color is not None and a.color != b.color:
            return False
        return True

    def _matches_existing(self, candidate: ObjectState, existing: list[ObjectState], det: Detection2D) -> bool:
        existing_ids = {obj.id for obj in existing}
        if candidate.id in existing_ids:
            return True

        # Strong spatial dedupe: a 2D detector and AprilTag likely saw the same physical item.
        for obj in existing:
            if self._same_semantic(candidate, obj) and self._distance_xy(candidate.pose, obj.pose) <= self.nearest_dedupe_distance_m:
                return True

        # Weak fallback only against trusted 3D objects when a detector is uncalibrated.
        # This preserves multiple 2D objects with the same class/color while keeping old
        # AprilTag-priority behavior when YOLO/LocateAnything sees a known tagged object.
        if self.homography is None:
            for obj in existing:
                if obj.source in {"limelight", "fake"} and self._same_semantic(candidate, obj):
                    return True
        return False

    def fuse(
        self,
        apriltag_scene: SceneGraph | None,
        yolo_detections: list[Detection2D] | None,
        locate_detections: list[Detection2D] | None,
    ) -> SceneGraph:
        warnings: list[str] = []
        if apriltag_scene is not None:
            objects = list(apriltag_scene.objects)
            workspace = apriltag_scene.workspace
            uncertainty = apriltag_scene.uncertainty
            world_frame = apriltag_scene.world_frame
            warnings.extend(apriltag_scene.warnings)
            if not apriltag_scene.objects:
                warnings.append("AprilTag anchor/workspace available, but no tagged objects were visible")
        else:
            objects = []
            workspace = self.workspace
            uncertainty = SensorUncertainty(position_std_m=0.03, rotation_std_deg=8.0)
            world_frame = "table_anchor" if self.homography else "approx_table"
            warnings.append("No AprilTag scene; fused scene uses 2D detections with approximate workspace")

        self.workspace = workspace

        detections: list[tuple[Detection2D, float]] = []
        detections.extend((det, 0.85 if self.homography else 0.50) for det in (yolo_detections or []))
        detections.extend((det, 0.70 if self.homography else 0.42) for det in (locate_detections or []))

        seen_tracks: set[tuple[str, int]] = set()
        index = 0
        for det, weight in detections:
            if det.track_id is not None:
                track_key = (det.source, det.track_id)
                if track_key in seen_tracks:
                    continue
                seen_tracks.add(track_key)
            candidate = self._det_to_obj(det, weight, index)
            index += 1
            if self._matches_existing(candidate, objects, det):
                continue
            objects.append(candidate)

        # If there is absolutely no perception input, keep the original offline demo usable.
        if apriltag_scene is None and not objects:
            base = FakePerceptionProvider().get_scene()
            base.warnings.append("No fused detections; using fake scene fallback")
            return base

        return SceneGraph(
            timestamp_s=time.time(),
            world_frame=world_frame,
            objects=objects,
            workspace=workspace,
            uncertainty=uncertainty,
            warnings=warnings,
        )
