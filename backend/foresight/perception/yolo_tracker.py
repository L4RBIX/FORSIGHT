from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from foresight.config import CONFIG, AppConfig
from foresight.schemas import Detection2D


@dataclass
class YoloTracker:
    config: AppConfig = field(default_factory=lambda: CONFIG)
    model_name: str | None = None
    _model: Any = field(default=None, init=False)
    available: bool = field(default=False, init=False)
    unavailable_reason: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if not self.config.enable_yolo:
            self.unavailable_reason = "YOLO disabled by config"
            return
        try:
            from ultralytics import YOLO  # type: ignore

            names = [self.model_name or self.config.yolo_model, *self.config.yolo_fallback_models]
            last_exc: Exception | None = None
            for name in names:
                try:
                    self._model = YOLO(name)
                    self.available = True
                    return
                except Exception as exc:  # weights may be missing offline
                    last_exc = exc
            self.unavailable_reason = str(last_exc)
        except Exception as exc:
            self.unavailable_reason = str(exc)

    def track_frame(self, frame: Any, stream_id: str = "default") -> list[Detection2D]:
        if not self.available or self._model is None:
            return []
        results = self._model.track(frame, persist=True, tracker=self.config.yolo_tracker)
        detections: list[Detection2D] = []
        for result in results or []:
            names = getattr(result, "names", {}) or {}
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            xyxy = getattr(boxes, "xyxy", [])
            conf = getattr(boxes, "conf", [])
            cls = getattr(boxes, "cls", [])
            ids = getattr(boxes, "id", None)
            for i, box in enumerate(xyxy):
                try:
                    vals = [float(v) for v in box.tolist()]
                except Exception:
                    vals = [float(v) for v in box]
                class_id = int(cls[i]) if len(cls) > i else -1
                label = str(names.get(class_id, class_id))
                tid = None
                if ids is not None and len(ids) > i:
                    tid = int(ids[i])
                detections.append(
                    Detection2D(
                        label=label,
                        class_name=label,
                        bbox_xyxy=tuple(vals),
                        point_xy=((vals[0] + vals[2]) / 2.0, (vals[1] + vals[3]) / 2.0),
                        confidence=float(conf[i]) if len(conf) > i else 0.5,
                        source="yolo",
                        track_id=tid,
                    )
                )
        return detections

    def reset_stream(self) -> None:
        # Ultralytics stores tracking state internally. Recreate model for unrelated streams.
        if self.available:
            self.__post_init__()
