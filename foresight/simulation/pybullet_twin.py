from __future__ import annotations

from dataclasses import dataclass, field

from foresight.schemas import ObjectState, SceneGraph

try:  # pragma: no cover - pybullet is optional in CI/demo zip creation.
    import pybullet as p  # type: ignore
except Exception:  # pragma: no cover
    p = None  # type: ignore


@dataclass
class PyBulletTwin:
    gui: bool = True
    client_id: int | None = field(default=None, init=False)
    object_bodies: dict[str, int] = field(default_factory=dict, init=False)
    available: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if p is None:
            self.available = False
            return
        mode = p.GUI if self.gui else p.DIRECT
        self.client_id = p.connect(mode)
        self.available = True
        p.setGravity(0, 0, -9.81, physicsClientId=self.client_id)

    def _create_body(self, obj: ObjectState) -> int:
        assert p is not None and self.client_id is not None
        sx, sy, sz = obj.size_m
        if obj.class_name in {"mug", "bottle"}:
            radius = max(sx, sy) / 2
            collision = p.createCollisionShape(p.GEOM_CYLINDER, radius=radius, height=sz, physicsClientId=self.client_id)
            visual = p.createVisualShape(p.GEOM_CYLINDER, radius=radius, length=sz, physicsClientId=self.client_id)
        else:
            half = [sx / 2, sy / 2, sz / 2]
            collision = p.createCollisionShape(p.GEOM_BOX, halfExtents=half, physicsClientId=self.client_id)
            visual = p.createVisualShape(p.GEOM_BOX, halfExtents=half, physicsClientId=self.client_id)
        return p.createMultiBody(
            baseMass=obj.mass_kg if obj.movable else 0.0,
            baseCollisionShapeIndex=collision,
            baseVisualShapeIndex=visual,
            basePosition=[obj.pose.x, obj.pose.y, obj.pose.z],
            physicsClientId=self.client_id,
        )

    def load_scene(self, scene: SceneGraph) -> None:
        if not self.available:
            return
        assert p is not None and self.client_id is not None
        p.resetSimulation(physicsClientId=self.client_id)
        p.setGravity(0, 0, -9.81, physicsClientId=self.client_id)
        wx = scene.workspace.x_max - scene.workspace.x_min
        wy = scene.workspace.y_max - scene.workspace.y_min
        center = [(scene.workspace.x_min + scene.workspace.x_max) / 2, (scene.workspace.y_min + scene.workspace.y_max) / 2, -0.01]
        table_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[wx / 2, wy / 2, 0.01], physicsClientId=self.client_id)
        table_vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[wx / 2, wy / 2, 0.01], physicsClientId=self.client_id)
        p.createMultiBody(baseMass=0, baseCollisionShapeIndex=table_col, baseVisualShapeIndex=table_vis, basePosition=center, physicsClientId=self.client_id)
        self.object_bodies.clear()
        for obj in scene.objects:
            self.object_bodies[obj.id] = self._create_body(obj)

    def update_scene(self, scene: SceneGraph) -> None:
        if not self.available:
            return
        assert p is not None and self.client_id is not None
        for obj in scene.objects:
            body = self.object_bodies.get(obj.id)
            if body is None:
                body = self._create_body(obj)
                self.object_bodies[obj.id] = body
            # Live twin mode: perception owns state; physics does not fight sensors.
            p.resetBasePositionAndOrientation(body, [obj.pose.x, obj.pose.y, obj.pose.z], [0, 0, 0, 1], physicsClientId=self.client_id)

    def snapshot(self) -> int:
        if not self.available:
            return -1
        assert p is not None and self.client_id is not None
        return int(p.saveState(physicsClientId=self.client_id))

    def restore(self, state_id: int) -> None:
        if not self.available or state_id < 0:
            return
        assert p is not None and self.client_id is not None
        p.restoreState(stateId=state_id, physicsClientId=self.client_id)

    def disconnect(self) -> None:
        if self.available and self.client_id is not None:
            assert p is not None
            p.disconnect(physicsClientId=self.client_id)
        self.available = False
