from __future__ import annotations

from pathlib import Path

import requests

from foresight.config import CONFIG, AppConfig
from foresight.schemas import Detection2D, LocateAnythingResult


class LocateAnythingClient:
    def __init__(self, config: AppConfig = CONFIG, base_url: str | None = None):
        self.config = config
        self.base_url = (base_url or config.locateanything_url).rstrip("/")

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=min(2.0, self.config.locateanything_timeout_s))
            return r.ok and bool(r.json().get("ok", True))
        except Exception:
            return False

    def scan_image(self, image_path: str | Path, query: str) -> LocateAnythingResult:
        path = Path(image_path)
        if not path.exists():
            return LocateAnythingResult(ok=False, query=query, error=f"Image not found: {path}")
        try:
            with path.open("rb") as f:
                response = requests.post(
                    f"{self.base_url}/locate",
                    files={"image": (path.name, f, "application/octet-stream")},
                    data={"query": query},
                    timeout=self.config.locateanything_timeout_s,
                )
            response.raise_for_status()
            data = response.json()
            detections = []
            for det in data.get("detections", []):
                try:
                    detections.append(Detection2D.model_validate(det))
                except Exception:
                    continue
            return LocateAnythingResult(ok=bool(data.get("ok", False)), query=data.get("query", query), detections=detections, error=data.get("error"), raw=data.get("raw"))
        except Exception as exc:
            return LocateAnythingResult(ok=False, query=query, error=str(exc))
