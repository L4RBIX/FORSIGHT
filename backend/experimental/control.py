"""
AprilTag-джойстик, сглаживание скорости и логирование тиков.
"""

from __future__ import annotations

import math
import time

import pybullet as p
import requests

from foresight.config import CONFIG
from world_model import SafetyBrain

LOOP_HZ = 8.0
LOOP_PERIOD = 1.0 / LOOP_HZ

LIMELIGHT_URL = CONFIG.limelight_results_url
LIMELIGHT_TIMEOUT = CONFIG.limelight_timeout_s

JOYSTICK_DEADZONE = 2.0
LIMELIGHT_MAX_DEG = 30.0
STICK_RESPONSE = 1.35

MAX_LINEAR = 3.0
MAX_ANGULAR = 0.55
MAX_REVERSE = -1.5

SMOOTH_ALPHA = 0.1
EMERGENCY_ALPHA = 0.45
TAG_LOST_ALPHA = 0.18
STOP_THRESHOLD = 0.03

KEY_LINEAR_STEP = 0.12
KEY_ANGULAR_STEP = 0.07

PHYSICS_STEPS_PER_TICK = 30


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class AprilTagJoystick:
    """Limelight AprilTag → виртуальный джойстик (tx/ty + Pose z)."""

    def __init__(self) -> None:
        self.limelight_active = False
        self._warned_fallback = False
        self._warned_tag_lost = False
        self.kb_target_linear = 0.0
        self.kb_target_angular = 0.0

    @staticmethod
    def _extract_pose_z(data: dict) -> float | None:
        for key in (
            "botpose_targetspace",
            "targetPoseCameraSpace",
            "targetpose_cameraspace",
            "botpose",
            "targetPoseRobotSpace",
        ):
            raw = data.get(key)
            if raw and isinstance(raw, (list, tuple)) and len(raw) >= 3:
                z = abs(float(raw[2]))
                if z > 0.01:
                    return z
        for key in ("tz", "z", "distance"):
            if key in data:
                z = abs(float(data[key]))
                if z > 0.01:
                    return z
        pose = data.get("targetPose") or data.get("pose")
        if isinstance(pose, dict) and "z" in pose:
            z = abs(float(pose["z"]))
            if z > 0.01:
                return z
        return None

    @staticmethod
    def _is_tag_valid(data: dict, ta: float) -> bool:
        if "tv" in data:
            return int(float(data["tv"])) == 1
        if "validTarget" in data:
            return bool(data["validTarget"])
        if "fiducials" in data and isinstance(data["fiducials"], list):
            return len(data["fiducials"]) > 0
        return ta > 0.05

    def _fetch_apriltag(self) -> dict | None:
        try:
            response = requests.get(LIMELIGHT_URL, timeout=LIMELIGHT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            tx = float(data.get("tx", 0.0))
            ty = float(data.get("ty", 0.0))
            ta = float(data.get("ta", 0.0))
            distance_z = self._extract_pose_z(data)
            tag_valid = self._is_tag_valid(data, ta)
            return {
                "tx": tx,
                "ty": ty,
                "ta": ta,
                "distance_z": distance_z,
                "tag_valid": tag_valid,
                "pose_source": "z" if distance_z is not None else "ta",
            }
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return None

    def _compute_targets(self, tx: float, ty: float) -> tuple[float, float, str]:
        if abs(tx) <= JOYSTICK_DEADZONE and abs(ty) <= JOYSTICK_DEADZONE:
            return 0.0, 0.0, "deadzone"

        target_linear = 0.0
        target_angular = 0.0
        span = LIMELIGHT_MAX_DEG - JOYSTICK_DEADZONE

        if ty > JOYSTICK_DEADZONE:
            stick = (ty - JOYSTICK_DEADZONE) / span
            target_linear = stick * MAX_LINEAR * STICK_RESPONSE
        elif ty < -JOYSTICK_DEADZONE:
            stick = (ty + JOYSTICK_DEADZONE) / span
            target_linear = stick * abs(MAX_REVERSE) * STICK_RESPONSE

        if tx < -JOYSTICK_DEADZONE:
            stick = (tx + JOYSTICK_DEADZONE) / span
            target_angular = stick * MAX_ANGULAR * STICK_RESPONSE
        elif tx > JOYSTICK_DEADZONE:
            stick = (tx - JOYSTICK_DEADZONE) / span
            target_angular = stick * MAX_ANGULAR * STICK_RESPONSE

        return (
            clamp(target_linear, MAX_REVERSE, MAX_LINEAR),
            clamp(target_angular, -MAX_ANGULAR, MAX_ANGULAR),
            "drive",
        )

    def _read_keyboard(self) -> dict:
        keys = p.getKeyboardEvents()
        if p.B3G_UP_ARROW in keys and keys[p.B3G_UP_ARROW] & p.KEY_IS_DOWN:
            self.kb_target_linear = clamp(
                self.kb_target_linear + KEY_LINEAR_STEP, MAX_REVERSE, MAX_LINEAR
            )
        if p.B3G_DOWN_ARROW in keys and keys[p.B3G_DOWN_ARROW] & p.KEY_IS_DOWN:
            self.kb_target_linear = clamp(
                self.kb_target_linear - KEY_LINEAR_STEP, MAX_REVERSE, MAX_LINEAR
            )
        if p.B3G_LEFT_ARROW in keys and keys[p.B3G_LEFT_ARROW] & p.KEY_IS_DOWN:
            self.kb_target_angular = clamp(
                self.kb_target_angular - KEY_ANGULAR_STEP, -MAX_ANGULAR, MAX_ANGULAR
            )
        if p.B3G_RIGHT_ARROW in keys and keys[p.B3G_RIGHT_ARROW] & p.KEY_IS_DOWN:
            self.kb_target_angular = clamp(
                self.kb_target_angular + KEY_ANGULAR_STEP, -MAX_ANGULAR, MAX_ANGULAR
            )

        return {
            "source": "keyboard",
            "target_linear": self.kb_target_linear,
            "target_angular": self.kb_target_angular,
            "ta": 0.0,
            "tx": 0.0,
            "ty": 0.0,
            "distance_z": None,
            "tag_valid": True,
            "pose_source": "manual",
            "mode": "manual",
        }

    def read_desired(self) -> dict:
        frame = self._fetch_apriltag()

        if frame is not None:
            if not frame["tag_valid"]:
                if not self._warned_tag_lost:
                    print("[CAMERA] AprilTag потерян — плавная остановка.")
                    self._warned_tag_lost = True
                self.limelight_active = True
                return {
                    "source": "limelight",
                    "target_linear": 0.0,
                    "target_angular": 0.0,
                    "tx": frame["tx"],
                    "ty": frame["ty"],
                    "ta": frame["ta"],
                    "distance_z": frame["distance_z"],
                    "tag_valid": False,
                    "pose_source": frame["pose_source"],
                    "mode": "tag_lost",
                }

            self._warned_tag_lost = False
            if not self.limelight_active:
                src = "Pose z" if frame["distance_z"] else "ta (fallback)"
                print(f"[CAMERA] AprilTag найден — дистанция: {src}")
            elif self._warned_fallback:
                print("[CAMERA] Limelight восстановлен.")
            self.limelight_active = True
            self._warned_fallback = False

            target_lin, target_ang, mode = self._compute_targets(frame["tx"], frame["ty"])
            return {
                "source": "limelight",
                "target_linear": target_lin,
                "target_angular": target_ang,
                "tx": frame["tx"],
                "ty": frame["ty"],
                "ta": frame["ta"],
                "distance_z": frame["distance_z"],
                "tag_valid": True,
                "pose_source": frame["pose_source"],
                "mode": mode,
            }

        if self.limelight_active or not self._warned_fallback:
            print("[CAMERA] Limelight недоступен — Plan B: стрелки (↑↓←→).")
            self._warned_fallback = True
        self.limelight_active = False
        return self._read_keyboard()


class VelocitySmoother:
    def __init__(self) -> None:
        self.motor_linear = 0.0
        self.motor_angular = 0.0

    def apply(
        self,
        final_linear: float,
        final_angular: float,
        emergency: bool = False,
        tag_lost: bool = False,
    ) -> tuple[float, float]:
        if emergency:
            alpha = EMERGENCY_ALPHA
        elif tag_lost:
            alpha = TAG_LOST_ALPHA
        else:
            alpha = SMOOTH_ALPHA

        self.motor_linear += alpha * (final_linear - self.motor_linear)
        self.motor_angular += alpha * (final_angular - self.motor_angular)

        if abs(self.motor_linear) < STOP_THRESHOLD:
            self.motor_linear = 0.0
        if abs(self.motor_angular) < STOP_THRESHOLD:
            self.motor_angular = 0.0

        return self.motor_linear, self.motor_angular


def log_tick(
    tick: int,
    desired: dict,
    brain: dict,
    motor_lin: float,
    motor_ang: float,
    x: float,
    y: float,
    yaw: float,
) -> None:
    src_map = {
        "limelight": "AprilTag",
        "keyboard": "Клавиатура",
        "deepseek": "DeepSeek Brain",
    }
    src = src_map.get(desired["source"], desired["source"])
    extra = ""
    if desired["source"] == "limelight":
        dist = desired.get("distance_z")
        dist_str = f"z={dist:.2f}м" if dist is not None else f"ta={desired['ta']:.1f}%"
        extra = (
            f" | tx={desired['tx']:.1f}° ty={desired['ty']:.1f}° "
            f"{dist_str} [{desired.get('pose_source', '')}]"
        )

    brain_tag = brain["status"]
    if brain["override"]:
        brain_tag = f"🧠 ПЕРЕХВАТ [{brain['status']}]"

    print(
        f"\n--- Тик {tick} | {src}{extra} ---\n"
        f"  desired=({desired['target_linear']:.2f}, {desired['target_angular']:.2f}) "
        f"[{desired.get('mode', '')}]\n"
        f"  brain  =({brain['final_linear']:.2f}, {brain['final_angular']:.2f}) "
        f"risk={brain['risk']:.0f}% | {brain_tag}\n"
        f"  motor  =({motor_lin:.2f}, {motor_ang:.2f}) | "
        f"pos=({x:.2f}, {y:.2f}) yaw={math.degrees(yaw):.0f}°"
    )

    if brain["override"]:
        print(f"  ⚠️  Мозг: {brain['reason']} | события: {brain['events']}")
    elif brain["status"] == "CAUTION":
        print(f"  ⚠️  Мозг: {brain['reason']}")
    elif desired.get("mode") == "tag_lost":
        print("  ⏸  AprilTag потерян — плавное торможение")
    elif desired.get("mode") == "deadzone":
        print("  ⏸  Мёртвая зона джойстика")
    else:
        print("  ✅ Мозг одобрил команду")
