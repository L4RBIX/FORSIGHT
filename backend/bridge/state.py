"""
Mirrors src/mock/mockEngine.ts: scanning -> predicting -> live, except driven
by real Limelight detections and your real PyBullet sim instead of scripted data.
"""
from __future__ import annotations

import asyncio
import time
from typing import Callable

from contract import ActionInfo, Prediction, SensorInfo, TelemetryFrame
from limelight_client import LimelightClient
from sim_adapter import run_simulation

SCAN_PHASE_S = 1.2
PREDICT_PHASE_S = 1.2
TICK_S = 1 / 12  # ~12Hz, matches the frontend's expected 10-15Hz

# Adjust to your actual rig's measured noise if you have it; shown as-is in the
# dashboard's UNCERTAINTY block either way.
DEFAULT_SENSOR = SensorInfo(pos_noise_mm=4.0, rot_noise_deg=1.8, tracking="ok")


class ForesightState:
    def __init__(self, limelight: LimelightClient, on_frame: Callable[[TelemetryFrame], None]):
        self.limelight = limelight
        self.on_frame = on_frame
        self.mode = "live"
        self.action: ActionInfo | None = None
        self.prediction: Prediction | None = None
        self._lock = asyncio.Lock()

    async def run_forever(self) -> None:
        """Background perception loop — always streams current detections at
        TICK_S, independent of whatever scan/predict phase a command started.

        get_detections()/get_camera_frame_data_url() read from caches that
        LimelightClient's own background threads keep fresh (see its module
        docstring), so these calls are fast and safe to make directly here —
        they never block on network I/O themselves."""
        while True:
            objects = self.limelight.get_detections()
            frame = TelemetryFrame(
                timestamp=time.time(),
                mode=self.mode,
                camera_frame=self.limelight.get_camera_frame_data_url(),
                objects=objects,
                sensor=DEFAULT_SENSOR,
                action=self.action if self.mode != "scanning" else None,
                prediction=self.prediction if self.mode == "live" else None,
            )
            self.on_frame(frame)
            await asyncio.sleep(TICK_S)

    async def handle_scan(self) -> None:
        async with self._lock:
            self.mode = "scanning"
            self.action = None
            self.prediction = None
            await asyncio.sleep(SCAN_PHASE_S)
            self.mode = "live"

    async def handle_propose_action(self, text: str) -> None:
        async with self._lock:
            self.mode = "scanning"
            self.prediction = None
            await asyncio.sleep(SCAN_PHASE_S)

            objects = self.limelight.get_detections()
            # Naive object match: does the action text mention a detected
            # object's label? Replace with whatever action-parsing you already
            # have (or an LLM call) if this is too crude.
            target = next((o for o in objects if o.label.lower() in text.lower()), None)
            self.action = ActionInfo(
                text=text,
                object_id=target.id if target else (objects[0].id if objects else None),
                dir=(1.0, 0.0, 0.0),
                force_n=3.0,
            )
            self.mode = "predicting"
            await asyncio.sleep(PREDICT_PHASE_S)

            # run_simulation is your PyBullet sim — likely CPU-bound and
            # potentially slow (Monte-Carlo rollouts), so it also runs off the
            # event loop thread rather than freezing frame broadcasts while it churns.
            self.prediction = await asyncio.to_thread(run_simulation, objects, self.action)
            self.mode = "live"
