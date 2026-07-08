"""
Ingests a Limelight 3/3A running a neural-detector pipeline, over plain HTTP —
no NetworkTables / roboRIO needed for a bench or table demo.

Two independent sources:
  - Detections: GET http://<host>:5807/results  (Limelight's JSON results dump)
  - Camera frame: MJPEG stream at http://<host>:5800/stream.mjpg, grabbed with OpenCV

FIELD NAMES MAY DRIFT ACROSS LL OS VERSIONS. If `get_detections()` comes back
empty with a neural pipeline actively running, run this file directly:

    python limelight_client.py

It prints the raw /results payload so you can see the actual keys your
firmware sends and adjust `_parse_detections` / `_bbox_from_det` below.

NOTE ON TIMEOUTS: `requests`' `timeout=` bounds the socket connect/read phases,
but on some platforms it does NOT reliably bound slow/hanging DNS resolution
(getaddrinfo can block well past it if the host is unreachable or misconfigured,
e.g. mDNS resolution failing for `limelight.local`). Both the detections poll
and the camera stream are therefore run on their own background threads that
just update a cache — get_detections()/get_camera_frame_data_url() always
return instantly from that cache, so a slow/stuck Limelight can never stall
frame delivery to the dashboard, only make the cache go briefly stale.
"""
from __future__ import annotations

import base64
import logging
import threading
import time
from dataclasses import dataclass

import cv2
import requests

from contract import DetectedObject

log = logging.getLogger("limelight")


@dataclass
class LimelightConfig:
    host: str = "limelight.local"  # or the camera's IP, e.g. "10.TE.AM.11"
    results_port: int = 5807
    stream_port: int = 5800
    results_timeout_s: float = 0.25


class LimelightClient:
    """Both the camera stream and the detections poll run on their own
    background threads, each just updating a cached value under a lock.
    get_detections() / get_camera_frame_data_url() read those caches and
    always return instantly — see the module docstring for why."""

    def __init__(self, config: LimelightConfig | None = None):
        self.config = config or LimelightConfig()
        self._latest_frame_jpeg: bytes | None = None
        self._frame_lock = threading.Lock()
        self._latest_objects: list[DetectedObject] = []
        self._objects_lock = threading.Lock()
        self._stop = threading.Event()
        self._stream_thread: threading.Thread | None = None
        self._detections_thread: threading.Thread | None = None

    def start(self) -> None:
        self._stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._stream_thread.start()
        self._detections_thread = threading.Thread(target=self._detections_loop, daemon=True)
        self._detections_thread.start()

    def stop(self) -> None:
        self._stop.set()
        for t in (self._stream_thread, self._detections_thread):
            if t:
                t.join(timeout=1)

    # -- camera stream (background thread) ---------------------------------

    def _stream_loop(self) -> None:
        url = f"http://{self.config.host}:{self.config.stream_port}/stream.mjpg"
        while not self._stop.is_set():
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                log.warning("Could not open Limelight stream at %s, retrying in 2s", url)
                time.sleep(2)
                continue
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    break
                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ok:
                    with self._frame_lock:
                        self._latest_frame_jpeg = buf.tobytes()
            cap.release()

    def get_camera_frame_data_url(self) -> str | None:
        with self._frame_lock:
            jpeg = self._latest_frame_jpeg
        if jpeg is None:
            return None
        return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")

    # -- detections (background thread) --------------------------------------

    def _detections_loop(self) -> None:
        url = f"http://{self.config.host}:{self.config.results_port}/results"
        session = requests.Session()
        while not self._stop.is_set():
            try:
                resp = session.get(url, timeout=self.config.results_timeout_s)
                resp.raise_for_status()
                objects = self._parse_detections(resp.json())
                with self._objects_lock:
                    self._latest_objects = objects
            except (requests.RequestException, ValueError) as exc:
                log.debug("Limelight results fetch failed: %s", exc)
                # Leave the cache as-is rather than flashing to empty on one
                # missed poll; a real disconnect will show as a stale/no-op
                # object list rather than objects flickering out and back in.
            self._stop.wait(0.05)

    def get_detections(self) -> list[DetectedObject]:
        with self._objects_lock:
            return list(self._latest_objects)

    def _parse_detections(self, raw: dict) -> list[DetectedObject]:
        # Some firmwares nest the payload under "Results", some don't.
        results = raw.get("Results", raw)
        detector = results.get("Detector", []) or []

        objects: list[DetectedObject] = []
        for i, det in enumerate(detector):
            label = det.get("class") or det.get("className") or "object"
            confidence = float(det.get("conf", det.get("confidence", 0.0)))

            # tx/ty are angular offsets (degrees) from the crosshair; ta is target
            # area as a % of the frame. Converting these to real table-plane
            # meters needs your camera's mount height/angle — do that math here
            # with your actual calibration. Left as a rough placeholder so the
            # pipeline runs end-to-end before you wire in real geometry.
            tx = float(det.get("tx", 0.0))
            ty = float(det.get("ty", 0.0))
            ta = float(det.get("ta", 0.01))

            pos = (tx / 30.0, ty / 30.0, 0.0)  # TODO: replace with calibrated table-plane pos
            size_guess = max(0.04, min(0.2, ta * 2))
            size = (size_guess, size_guess, size_guess)

            objects.append(
                DetectedObject(
                    id=f"{label}_{i + 1}",
                    label=label,
                    confidence=confidence,
                    pos=pos,
                    size=size,
                    movable=True,
                    near_edge=abs(pos[0]) > 0.32 or abs(pos[1]) > 0.22,
                    bbox=self._bbox_from_det(det),
                )
            )
        return objects

    @staticmethod
    def _bbox_from_det(det: dict) -> tuple[float, float, float, float]:
        corners = [det.get(f"corner{i}_X") for i in range(4)]
        if all(c is not None for c in corners):
            xs = [det[f"corner{i}_X"] for i in range(4)]
            ys = [det[f"corner{i}_Y"] for i in range(4)]
            x0, x1 = min(xs) / 1280.0, max(xs) / 1280.0
            y0, y1 = min(ys) / 720.0, max(ys) / 720.0
            return (x0, y0, x1 - x0, y1 - y0)
        # Fallback: rough box centered on tx/ty when corner points aren't present.
        cx = 0.5 + float(det.get("tx", 0.0)) / 60.0
        cy = 0.5 + float(det.get("ty", 0.0)) / 45.0
        w = h = max(0.05, float(det.get("ta", 0.02)) * 3)
        return (cx - w / 2, cy - h / 2, w, h)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = LimelightConfig()
    r = requests.get(f"http://{cfg.host}:{cfg.results_port}/results", timeout=2)
    print(r.text)
