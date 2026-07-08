from __future__ import annotations

import random

from foresight.schemas import Pose3D, SensorUncertainty


def sample_pose(pose: Pose3D, uncertainty: SensorUncertainty, rng: random.Random) -> Pose3D:
    return Pose3D(
        x=rng.gauss(pose.x, uncertainty.position_std_m),
        y=rng.gauss(pose.y, uncertainty.position_std_m),
        z=max(0.0, rng.gauss(pose.z, uncertainty.position_std_m)),
        roll=rng.gauss(pose.roll, uncertainty.rotation_std_deg),
        pitch=rng.gauss(pose.pitch, uncertainty.rotation_std_deg),
        yaw=rng.gauss(pose.yaw, uncertainty.rotation_std_deg),
    )
