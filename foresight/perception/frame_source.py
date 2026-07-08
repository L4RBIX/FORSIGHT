"""Frame sources for optional local vision modules.

All frame sources are best-effort adapters. They return a FramePacket with
``frame=None`` and warnings instead of crashing the perception pipeline when
OpenCV, a camera, or a stream is unavailable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(slots=True)
class FramePacket:
    frame: Any | None
    source: str
    timestamp_s: float = field(default_factory=time.time)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.frame is not None


@runtime_checkable
class FrameSource(Protocol):
    def read_frame(self) -> FramePacket:
        """Return a single frame packet. Implementations must not block forever."""

    def close(self) -> None:
        """Release underlying resources if any."""


class _Cv2VideoCaptureSource:
    def __init__(self, source: int | str, name: str):
        self.source = source
        self.name = name
        self._cap: Any | None = None
        self._cv2_error: str | None = None

    def _cv2(self) -> Any | None:
        try:
            import cv2  # type: ignore

            return cv2
        except Exception as exc:  # pragma: no cover - depends on local install
            self._cv2_error = str(exc)
            return None

    def _ensure_cap(self) -> Any | None:
        if self._cap is not None:
            return self._cap
        cv2 = self._cv2()
        if cv2 is None:
            return None
        try:
            self._cap = cv2.VideoCapture(self.source)
            return self._cap
        except Exception as exc:  # pragma: no cover - defensive adapter
            self._cv2_error = str(exc)
            self._cap = None
            return None

    def read_frame(self) -> FramePacket:
        cap = self._ensure_cap()
        if cap is None:
            return FramePacket(frame=None, source=self.name, warnings=[f"OpenCV unavailable for {self.name}: {self._cv2_error}"])
        try:
            ok, frame = cap.read()
        except Exception as exc:
            return FramePacket(frame=None, source=self.name, warnings=[f"{self.name} read failed: {exc}"])
        if not ok or frame is None:
            return FramePacket(frame=None, source=self.name, warnings=[f"{self.name} returned no frame"])
        return FramePacket(frame=frame, source=self.name)

    def close(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None


class WebcamFrameSource(_Cv2VideoCaptureSource):
    def __init__(self, camera_index: int = 0):
        super().__init__(camera_index, name=f"webcam:{camera_index}")


class MjpegFrameSource(_Cv2VideoCaptureSource):
    def __init__(self, stream_url: str):
        super().__init__(stream_url, name=f"mjpeg:{stream_url}")


class ImageFileFrameSource:
    def __init__(self, image_path: str | Path):
        self.image_path = Path(image_path)

    def read_frame(self) -> FramePacket:
        if not self.image_path.exists():
            return FramePacket(frame=None, source=f"image:{self.image_path}", warnings=[f"Image file not found: {self.image_path}"])
        try:
            import cv2  # type: ignore

            frame = cv2.imread(str(self.image_path))
            if frame is None:
                return FramePacket(frame=None, source=f"image:{self.image_path}", warnings=[f"OpenCV could not read image: {self.image_path}"])
            return FramePacket(frame=frame, source=f"image:{self.image_path}")
        except Exception as cv_exc:
            try:
                from PIL import Image  # type: ignore
                import numpy as np  # type: ignore

                frame = np.asarray(Image.open(self.image_path).convert("RGB"))
                return FramePacket(frame=frame, source=f"image:{self.image_path}")
            except Exception as pil_exc:  # pragma: no cover - depends on optional deps
                return FramePacket(
                    frame=None,
                    source=f"image:{self.image_path}",
                    warnings=[f"Could not read image with cv2 ({cv_exc}) or PIL ({pil_exc})"],
                )

    def close(self) -> None:
        return None


class FakeFrameSource:
    def __init__(self, frame: Any | None = None, width: int = 640, height: int = 480):
        self._frame = frame
        self.width = width
        self.height = height

    def read_frame(self) -> FramePacket:
        if self._frame is not None:
            return FramePacket(frame=self._frame, source="fake_frame")
        try:
            import numpy as np  # type: ignore

            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        except Exception:  # numpy is in requirements, but keep CI-safe fallback
            frame = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]
        return FramePacket(frame=frame, source="fake_frame")

    def close(self) -> None:
        return None
