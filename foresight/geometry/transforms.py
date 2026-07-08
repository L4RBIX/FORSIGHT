from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from foresight.schemas import Pose3D


def _angle_to_rad(angle: float) -> float:
    # Limelight pose arrays commonly report rotations in degrees; tolerate radians too.
    return math.radians(angle) if abs(angle) > 2 * math.pi else angle


def pose_array_to_matrix(values: Sequence[float]) -> np.ndarray:
    if len(values) < 6:
        raise ValueError("Pose array must have at least six values: x,y,z,roll,pitch,yaw")
    x, y, z, roll, pitch, yaw = [float(v) for v in values[:6]]
    r, p, yw = map(_angle_to_rad, (roll, pitch, yaw))
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(yw), math.sin(yw)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]], dtype=float)
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]], dtype=float)
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]], dtype=float)
    mat = np.eye(4, dtype=float)
    mat[:3, :3] = rz @ ry @ rx
    mat[:3, 3] = [x, y, z]
    return mat


def matrix_to_pose(mat: np.ndarray) -> Pose3D:
    if mat.shape != (4, 4):
        raise ValueError("Expected 4x4 transform")
    x, y, z = mat[:3, 3].tolist()
    sy = math.sqrt(mat[0, 0] ** 2 + mat[1, 0] ** 2)
    singular = sy < 1e-6
    if not singular:
        roll = math.atan2(mat[2, 1], mat[2, 2])
        pitch = math.atan2(-mat[2, 0], sy)
        yaw = math.atan2(mat[1, 0], mat[0, 0])
    else:
        roll = math.atan2(-mat[1, 2], mat[1, 1])
        pitch = math.atan2(-mat[2, 0], sy)
        yaw = 0.0
    return Pose3D(x=float(x), y=float(y), z=float(z), roll=math.degrees(roll), pitch=math.degrees(pitch), yaw=math.degrees(yaw))


def camera_to_world_object_pose(cam_anchor_pose: Sequence[float], cam_obj_pose: Sequence[float]) -> Pose3D:
    t_cam_anchor = pose_array_to_matrix(cam_anchor_pose)
    t_cam_obj = pose_array_to_matrix(cam_obj_pose)
    t_world_obj = np.linalg.inv(t_cam_anchor) @ t_cam_obj
    return matrix_to_pose(t_world_obj)
