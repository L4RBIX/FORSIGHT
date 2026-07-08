from __future__ import annotations

import statistics
import time
from collections import defaultdict, deque
from typing import Any

import requests

from foresight.config import CONFIG, AppConfig
from foresight.geometry.transforms import camera_to_world_object_pose, matrix_to_pose, pose_array_to_matrix
from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.schemas import ObjectState, Pose3D, SceneGraph, SensorUncertainty, WorkspaceBounds


class LimelightError(RuntimeError):
    pass


class LimelightPerceptionProvider:
    def __init__(self, config: AppConfig = CONFIG):
        self.config = config
        self._smoothed: dict[str, Pose3D] = {}
        self._history: dict[str, deque[Pose3D]] = defaultdict(lambda: deque(maxlen=30))
        self._fallback = FakePerceptionProvider()

    def _fetch(self) -> dict[str, Any]:
        response = requests.get(self.config.limelight_results_url, timeout=self.config.limelight_timeout_s)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _fiducials(data: dict[str, Any]) -> list[dict[str, Any]]:
        results = data.get("Results", data)
        fid = results.get("Fiducial") or results.get("Fiducials") or data.get("Fiducial") or []
        if isinstance(fid, dict):
            fid = [fid]
        return [f for f in fid if isinstance(f, dict)]

    @staticmethod
    def _pose_from_fid(fid: dict[str, Any]) -> list[float] | None:
        for key in ("t6t_cs", "t6c_ts", "t6r_fs", "t6r_ts", "t6t_rs"):
            value = fid.get(key)
            if isinstance(value, list) and len(value) >= 6:
                return [float(v) for v in value[:6]]
        return None

    def _smooth(self, object_id: str, pose: Pose3D) -> Pose3D:
        prev = self._smoothed.get(object_id)
        a = self.config.limelight_ema_alpha
        if prev is None:
            smoothed = pose
        else:
            smoothed = Pose3D(
                x=a * pose.x + (1 - a) * prev.x,
                y=a * pose.y + (1 - a) * prev.y,
                z=a * pose.z + (1 - a) * prev.z,
                roll=a * pose.roll + (1 - a) * prev.roll,
                pitch=a * pose.pitch + (1 - a) * prev.pitch,
                yaw=a * pose.yaw + (1 - a) * prev.yaw,
            )
        self._smoothed[object_id] = smoothed
        self._history[object_id].append(smoothed)
        return smoothed

    def _uncertainty(self) -> SensorUncertainty:
        xs = []
        ys = []
        zs = []
        yaws = []
        for hist in self._history.values():
            if len(hist) >= 3:
                xs.extend(p.x for p in hist)
                ys.extend(p.y for p in hist)
                zs.extend(p.z for p in hist)
                yaws.extend(p.yaw for p in hist)
        if len(xs) >= 3:
            pos = max(statistics.pstdev(xs), statistics.pstdev(ys), statistics.pstdev(zs), 0.003)
            rot = max(statistics.pstdev(yaws), 1.0)
            return SensorUncertainty(position_std_m=min(pos, 0.05), rotation_std_deg=min(rot, 10.0))
        return SensorUncertainty()

    def get_scene(self) -> SceneGraph:
        try:
            data = self._fetch()
            fids = self._fiducials(data)
        except Exception as exc:
            if self.config.limelight_fake_on_error:
                scene = self._fallback.get_scene()
                scene.warnings.append(f"Limelight unavailable; using fake fallback: {exc}")
                return scene
            raise LimelightError(str(exc)) from exc

        anchor_pose = None
        tag_poses: dict[int, list[float]] = {}
        for fid in fids:
            tag_id = fid.get("fID", fid.get("fid", fid.get("id")))
            if tag_id is None:
                continue
            try:
                tag_id_int = int(tag_id)
            except Exception:
                continue
            pose = self._pose_from_fid(fid)
            if pose is None:
                continue
            tag_poses[tag_id_int] = pose
            if tag_id_int == 0:
                anchor_pose = pose

        objects: list[ObjectState] = []
        warnings: list[str] = []
        world_frame = "table_anchor" if anchor_pose is not None else "camera"
        if anchor_pose is None:
            warnings.append("Anchor tag 0 missing; returning degraded camera-frame scene")

        for tag_id, pose_values in tag_poses.items():
            meta = self.config.tag_object_map.get(tag_id)
            if not meta or meta.get("role") == "anchor":
                continue
            pose = camera_to_world_object_pose(anchor_pose, pose_values) if anchor_pose is not None else matrix_to_pose(pose_array_to_matrix(pose_values))
            object_id = str(meta.get("id", f"tag_{tag_id}"))
            pose = self._smooth(object_id, pose)
            objects.append(
                ObjectState(
                    id=object_id,
                    label=f"{meta.get('color', '')} {meta.get('class', 'object')}".strip(),
                    class_name=str(meta.get("class", "object")),
                    color=meta.get("color"),
                    pose=pose,
                    size_m=tuple(meta.get("size_m", [0.08, 0.08, 0.08])),
                    mass_kg=float(meta.get("mass_kg", 0.1)),
                    movable=bool(meta.get("movable", True)),
                    confidence=0.85,
                    source="limelight",
                    tag_id=tag_id,
                )
            )

        return SceneGraph(
            timestamp_s=time.time(),
            world_frame=world_frame,
            objects=objects,
            workspace=WorkspaceBounds(x_min=-0.45, x_max=0.45, y_min=-0.30, y_max=0.30, z_min=0.0, z_max=0.60),
            uncertainty=self._uncertainty(),
            warnings=warnings,
        )
