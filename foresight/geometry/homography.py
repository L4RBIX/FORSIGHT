from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np


class HomographyProjector:
    def __init__(self, image_points: Sequence[Sequence[float]], world_points_m: Sequence[Sequence[float]]):
        if len(image_points) < 4 or len(world_points_m) < 4:
            raise ValueError("At least 4 image/world point pairs are required")
        self.image_points = np.asarray(image_points, dtype=float)
        self.world_points_m = np.asarray(world_points_m, dtype=float)
        self.h = self._fit(self.image_points, self.world_points_m)

    @staticmethod
    def _fit(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
        rows = []
        for (x, y), (u, v) in zip(src, dst, strict=False):
            rows.append([-x, -y, -1, 0, 0, 0, x * u, y * u, u])
            rows.append([0, 0, 0, -x, -y, -1, x * v, y * v, v])
        _, _, vh = np.linalg.svd(np.asarray(rows, dtype=float))
        h = vh[-1].reshape(3, 3)
        return h / h[2, 2]

    @classmethod
    def from_file(cls, path: str | Path) -> "HomographyProjector":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data["image_points"], data["world_points_m"])

    def image_point_to_table_xy(self, point_xy: Sequence[float]) -> tuple[float, float]:
        p = np.array([float(point_xy[0]), float(point_xy[1]), 1.0])
        mapped = self.h @ p
        mapped = mapped / mapped[2]
        return (float(mapped[0]), float(mapped[1]))
