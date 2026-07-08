import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from foresight.config import settings
from foresight.decision.safety_gate import SafetyGate

ws_router = APIRouter()


def _telemetry_frame(action_text: str | None = None) -> dict:
    gate = SafetyGate(block_threshold=settings.risk_block_threshold)
    risk_report = gate.decide(
        failures=26,
        simulations=settings.monte_carlo_runs,
        reason="Mug likely falls from table",
    )
    verdict = "SAFE" if risk_report.decision == "ALLOW" else risk_report.decision
    action = {
        "text": action_text or "push the blue box to the right",
        "object_id": "box_2",
        "dir": [1.0, 0.0, 0.0],
        "force_n": 4.0,
    }
    objects = [
        {
            "id": "box_2",
            "label": "blue box",
            "confidence": 0.91,
            "pos": [0.32, 0.11, 0.04],
            "size": [0.16, 0.12, 0.08],
            "movable": True,
            "near_edge": False,
            "bbox": [0.22, 0.48, 0.18, 0.16],
        },
        {
            "id": "mug_1",
            "label": "white mug",
            "confidence": 0.88,
            "pos": [0.56, 0.12, 0.05],
            "size": [0.08, 0.08, 0.10],
            "movable": True,
            "near_edge": True,
            "bbox": [0.63, 0.44, 0.10, 0.18],
        },
    ]
    return {
        "timestamp": time.time(),
        "mode": "live",
        "camera_frame": None,
        "objects": objects,
        "sensor": {
            "pos_noise_mm": 4.0,
            "rot_noise_deg": 1.8,
            "tracking": "ok" if settings.use_mock else "degraded",
        },
        "action": action,
        "prediction": {
            "risk": risk_report.risk_percent / 100,
            "verdict": verdict,
            "outcome": "mug falls from table",
            "reason": risk_report.reason,
            "n_sims": risk_report.evidence.simulations,
            "trajectories": [
                [[0.32, 0.11, 0.04], [0.40, 0.12, 0.04], [0.50, 0.13, 0.04]],
                [[0.56, 0.12, 0.05], [0.61, 0.15, 0.04], [0.72, 0.20, -0.18]],
            ],
            "safety_rule": f"BLOCK if predicted failure risk > {settings.risk_block_threshold:.0%}",
        },
        "scene": {"objects": objects},
        "risk": risk_report.model_dump(),
        "uncertainty": {
            "sensor_position_mm": 4.0,
            "sensor_rotation_deg": 1.8,
            "mass": "sampled from range",
            "friction": "sampled from range",
        },
    }


async def _stream_scene(websocket: WebSocket):
    await websocket.accept()
    action_text: str | None = None
    try:
        while True:
            try:
                command = await asyncio.wait_for(websocket.receive_json(), timeout=0.25)
                if command.get("type") == "propose_action":
                    action_text = str(command.get("text") or "").strip() or action_text
            except asyncio.TimeoutError:
                pass
            await websocket.send_json(_telemetry_frame(action_text))
    except WebSocketDisconnect:
        return


@ws_router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    await _stream_scene(websocket)


@ws_router.websocket("/ws/scene")
async def scene_websocket(websocket: WebSocket):
    await _stream_scene(websocket)
