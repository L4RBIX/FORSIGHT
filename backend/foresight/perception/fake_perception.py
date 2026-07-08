from __future__ import annotations

import time

from foresight.schemas import ObjectState, Pose3D, SceneGraph, SensorUncertainty, WorkspaceBounds


class FakePerceptionProvider:
    """Deterministic tabletop scene for demos and tests.

    The mug is deliberately near the table edge so consequence simulation can
    demonstrate non-zero risk for commands that push objects toward it.
    """

    def get_scene(self) -> SceneGraph:
        workspace = WorkspaceBounds(x_min=-0.45, x_max=0.45, y_min=-0.30, y_max=0.30, z_min=0.0, z_max=0.60)
        objects = [
            ObjectState(
                id="obj_blue_box",
                label="blue box",
                class_name="box",
                color="blue",
                pose=Pose3D(x=0.00, y=0.00, z=0.04),
                size_m=(0.08, 0.08, 0.08),
                mass_kg=0.15,
                movable=True,
                confidence=0.99,
                source="fake",
                tag_id=1,
            ),
            ObjectState(
                id="obj_red_box",
                label="red box",
                class_name="box",
                color="red",
                pose=Pose3D(x=-0.18, y=0.05, z=0.04),
                size_m=(0.08, 0.08, 0.08),
                mass_kg=0.15,
                movable=True,
                confidence=0.99,
                source="fake",
                tag_id=2,
            ),
            ObjectState(
                id="obj_mug",
                label="white mug near edge",
                class_name="mug",
                color="white",
                pose=Pose3D(x=0.37, y=0.21, z=0.05),
                size_m=(0.07, 0.07, 0.10),
                mass_kg=0.12,
                movable=True,
                confidence=0.95,
                source="fake",
                tag_id=3,
            ),
        ]
        return SceneGraph(
            timestamp_s=time.time(),
            world_frame="table_anchor",
            objects=objects,
            workspace=workspace,
            uncertainty=SensorUncertainty(position_std_m=0.006, rotation_std_deg=2.0),
        )
