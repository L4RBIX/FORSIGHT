"""Runtime configuration for Foresight.

The project is offline-first. Every external URL, model name, and feature flag is
kept here so the core demo path never depends on hardcoded infrastructure.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


DEFAULT_TAG_OBJECT_MAP: dict[int, dict[str, Any]] = {
    0: {"role": "anchor", "label": "table anchor"},
    1: {"id": "obj_blue_box", "class": "box", "color": "blue", "size_m": [0.08, 0.08, 0.08], "mass_kg": 0.15},
    2: {"id": "obj_red_box", "class": "box", "color": "red", "size_m": [0.08, 0.08, 0.08], "mass_kg": 0.15},
    3: {"id": "obj_mug", "class": "mug", "color": "white", "size_m": [0.07, 0.07, 0.10], "mass_kg": 0.12},
}


@dataclass(slots=True)
class AppConfig:
    # Limelight
    limelight_results_url: str = os.getenv("LIMELIGHT_RESULTS_URL", "http://172.29.0.1:5807/results")
    limelight_timeout_s: float = _float("LIMELIGHT_TIMEOUT_S", 0.25)
    limelight_ema_alpha: float = _float("LIMELIGHT_EMA_ALPHA", 0.55)
    limelight_fake_on_error: bool = _bool("LIMELIGHT_FAKE_ON_ERROR", True)
    limelight_mjpeg_url: str = os.getenv("LIMELIGHT_MJPEG_URL", "http://172.29.0.1:5800/stream.mjpg")
    webcam_index: int = _int("WEBCAM_INDEX", 0)

    # Semantic visual grounding service
    locateanything_url: str = os.getenv("LOCATEANYTHING_URL", "https://your-ngrok-url.ngrok-free.app")
    locateanything_timeout_s: float = _float("LOCATEANYTHING_TIMEOUT_S", 8.0)
    enable_locateanything: bool = _bool("ENABLE_LOCATEANYTHING", False)

    # Local object tracker
    enable_yolo: bool = _bool("ENABLE_YOLO", False)
    yolo_model: str = os.getenv("YOLO_MODEL", "yolo26n.pt")
    yolo_fallback_models: tuple[str, ...] = ("yolo11n.pt", "yolov8n.pt")
    yolo_tracker: str = os.getenv("YOLO_TRACKER", "bytetrack.yaml")

    # Safety policy
    max_force_n: float = _float("MAX_FORCE_N", 8.0)
    max_distance_m: float = _float("MAX_DISTANCE_M", 0.30)
    max_speed_mps: float = _float("MAX_SPEED_MPS", 0.30)
    max_fall_prob: float = _float("MAX_FALL_PROB", 0.20)
    max_collision_prob: float = _float("MAX_COLLISION_PROB", 0.20)
    max_boundary_prob: float = _float("MAX_BOUNDARY_PROB", 0.20)
    forbidden_classes: set[str] = field(default_factory=lambda: {"person", "human", "hand", "face", "animal", "knife"})

    # Simulation
    oracle_rollouts: int = _int("ORACLE_ROLLOUTS", 30)
    oracle_fast_rollouts: int = _int("ORACLE_FAST_ROLLOUTS", 12)
    oracle_seed: int = _int("ORACLE_SEED", 7)
    simulation_dt_s: float = _float("SIMULATION_DT_S", 1.0 / 240.0)
    simulation_duration_s: float = _float("SIMULATION_DURATION_S", 4.0)

    # Robot bridge
    robot_http_url: str = os.getenv("ROBOT_HTTP_URL", "http://127.0.0.1:8080/execute")
    robot_http_timeout_s: float = _float("ROBOT_HTTP_TIMEOUT_S", 1.5)
    robot_serial_port: str = os.getenv("ROBOT_SERIAL_PORT", "")
    robot_serial_baud: int = _int("ROBOT_SERIAL_BAUD", 115200)

    # Runtime storage
    run_log_path: Path = Path(os.getenv("RUN_LOG_PATH", "runs/demo_log.jsonl"))
    calibration_file: Path | None = Path(os.getenv("HOMOGRAPHY_CALIBRATION_FILE")) if os.getenv("HOMOGRAPHY_CALIBRATION_FILE") else None

    # Tag map can be overridden with JSON object whose keys are tag IDs.
    tag_object_map: dict[int, dict[str, Any]] = field(default_factory=lambda: DEFAULT_TAG_OBJECT_MAP.copy())

    @classmethod
    def from_env(cls) -> "AppConfig":
        cfg = cls()
        raw = os.getenv("TAG_OBJECT_MAP_JSON")
        if raw:
            try:
                parsed = json.loads(raw)
                cfg.tag_object_map = {int(k): v for k, v in parsed.items()}
            except Exception:
                # Keep safe defaults on malformed operator input.
                pass
        return cfg


CONFIG = AppConfig.from_env()


class Settings:
    """Small API settings surface for the FastAPI demo backend."""

    use_mock: bool = _bool("USE_MOCK", True)
    limelight_host: str | None = os.getenv("LIMELIGHT_HOST")
    locateanything_endpoint: str | None = os.getenv("LOCATEANYTHING_ENDPOINT")
    claude_api_key: str | None = os.getenv("CLAUDE_API_KEY")
    risk_block_threshold: float = _float("RISK_BLOCK_THRESHOLD", 0.30)
    monte_carlo_runs: int = _int("MONTE_CARLO_RUNS", 30)
    simulation_seconds: float = _float("SIMULATION_SECONDS", 4.0)


settings = Settings()
