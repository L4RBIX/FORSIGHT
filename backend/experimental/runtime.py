"""
Foresight Runtime — объединяет камеру, YOLO, DeepSeek, PyBullet SafetyBrain.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import pybullet as p

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from deepseek_brain import ActiveDriveOverride, BrainPlan, DeepSeekBrain
from foresight.config import AppConfig

CONFIG = AppConfig.from_env()
from foresight.main import ForesightPipeline
from foresight.perception.fusion_provider import FusionPerceptionProvider
from foresight.perception.limelight_client import LimelightPerceptionProvider
from foresight.perception.yolo_tracker import YoloTracker
from control import (
    AprilTagJoystick,
    LOOP_PERIOD,
    PHYSICS_STEPS_PER_TICK,
    VelocitySmoother,
    log_tick,
)
from world_model import DigitalTwin, PASSAGE_GAP, SafetyBrain

TEXT_COMMAND_FILE = Path(os.getenv("TEXT_COMMAND_FILE", "runs/text_command.txt"))
PERCEPTION_EVERY_N = int(os.getenv("PERCEPTION_EVERY_N", "4"))


class TextCommandQueue:
    """Читает команды из файла runs/text_command.txt (одна строка = одна команда)."""

    def __init__(self, path: Path = TEXT_COMMAND_FILE) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._startup_command = os.getenv("FORESIGHT_TEXT_COMMAND", "").strip()

    def poll(self) -> str | None:
        if self._startup_command:
            cmd = self._startup_command
            self._startup_command = ""
            return cmd

        if not self.path.exists():
            return None
        try:
            text = self.path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        if not text:
            return None
        try:
            self.path.write_text("", encoding="utf-8")
        except OSError:
            pass
        return text


class ForesightRuntime:
    def __init__(self, initial_text: str | None = None) -> None:
        self.twin = DigitalTwin(use_gui=True)
        self.camera = AprilTagJoystick()
        self.safety_brain = SafetyBrain(self.twin)
        self.smoother = VelocitySmoother()
        self.deepseek = DeepSeekBrain()
        self.text_queue = TextCommandQueue()
        if initial_text:
            self.text_queue._startup_command = initial_text.strip()

        self.perception = self._build_perception()
        self.pipeline = ForesightPipeline(
            perception_provider=self.perception,
            config=CONFIG,
        )
        self.drive_override: ActiveDriveOverride | None = None
        self.last_scene_summary = "scene unavailable"
        self.tick = 0
        self._yolo_status_printed = False

    def _build_perception(self) -> FusionPerceptionProvider:
        apriltag = LimelightPerceptionProvider(CONFIG)
        yolo = YoloTracker(CONFIG)
        return FusionPerceptionProvider(
            apriltag_provider=apriltag,
            yolo_tracker=yolo,
            config=CONFIG,
            use_fake_when_empty=True,
        )

    def _print_banner(self) -> None:
        yolo = self.perception.yolo_tracker
        yolo_line = "выкл"
        if CONFIG.enable_yolo:
            if yolo and yolo.available:
                yolo_line = f"вкл ({yolo.model_name or CONFIG.yolo_model})"
            else:
                yolo_line = f"ошибка: {getattr(yolo, 'unavailable_reason', '?')}"

        brain_line = "DeepSeek API" if self.deepseek.available else "локальный парсер (задайте DEEPSEEK_API_KEY)"

        print("=" * 60)
        print("  FORESIGHT — Camera + YOLO + DeepSeek Brain + PyBullet")
        print(f"  Limelight: {CONFIG.limelight_results_url}")
        print(f"  YOLO: {yolo_line}")
        print(f"  Мозг: {brain_line}")
        print(f"  Текст: {TEXT_COMMAND_FILE} или --text \"команда\"")
        print(f"  Pose z < {SafetyBrain.STOP_DISTANCE_M} м → E-stop")
        print(f"  Проход: {PASSAGE_GAP:.2f} м | Ctrl+C — выход")
        print("=" * 60)

    def _update_scene(self) -> None:
        if self.tick % PERCEPTION_EVERY_N != 0:
            return
        try:
            scene = self.perception.get_scene()
            labels = [obj.label for obj in scene.objects[:6]]
            self.last_scene_summary = f"{len(scene.objects)} obj: {', '.join(labels) or 'empty'}"
            if CONFIG.enable_yolo and not self._yolo_status_printed:
                yolo = self.perception.yolo_tracker
                if yolo and yolo.available:
                    print(f"[YOLO] Трекер активен: {yolo.model_name or CONFIG.yolo_model}")
                else:
                    print(f"[YOLO] Недоступен: {getattr(yolo, 'unavailable_reason', '?')}")
                self._yolo_status_printed = True
        except Exception as exc:
            self.last_scene_summary = f"perception error: {exc}"

    def _apply_brain_plan(self, plan: BrainPlan) -> None:
        print(f"\n[BRAIN] Команда «{plan.raw_command}» → mode={plan.mode} ({plan.source})")
        print(f"        {plan.reason}")

        if plan.mode == "stop":
            self.drive_override = None
            return

        if plan.mode == "drive":
            expires = time.time() + max(plan.duration_sec, 1.0)
            self.drive_override = ActiveDriveOverride(plan=plan, expires_at=expires)
            print(
                f"        Drive override: lin={plan.target_linear:.2f} "
                f"ang={plan.target_angular:.2f} на {plan.duration_sec:.0f}s"
            )
            return

        if plan.mode in ("manipulate", "scan"):
            cmd = plan.manipulation_text or plan.raw_command
            try:
                result = self.pipeline.evaluate_command(cmd)
                self.deepseek.attach_pipeline_result(plan, result)
                sim = result.simulation
                safety = result.safety
                print(f"        Foresight: {result.planning.status} | safety={safety.status}")
                if sim:
                    print(
                        f"        Симуляция: {sim.verdict} "
                        f"fall={sim.fall_probability:.0%} "
                        f"collision={sim.collision_probability:.0%}"
                    )
                if safety.allowed and plan.mode == "manipulate":
                    print("        ⚠ manipulate в Husky-demo: используйте drive-команды для прохода.")
            except Exception as exc:
                print(f"        Foresight pipeline ошибка: {exc}")

    def _poll_text_commands(self) -> None:
        cmd = self.text_queue.poll()
        if not cmd:
            return
        x, y, yaw = self.twin.get_robot_pose()
        context = {
            "robot_pose": {"x": x, "y": y, "yaw_deg": yaw * 57.2958},
            "scene": self.last_scene_summary,
            "passage_gap_m": PASSAGE_GAP,
        }
        plan = self.deepseek.interpret(cmd, context)
        self._apply_brain_plan(plan)

    def _resolve_desired(self, desired: dict) -> dict:
        """Камера ведёт; DeepSeek drive-override временно перекрывает."""
        now = time.time()
        if self.drive_override and self.drive_override.is_active(now):
            lin, ang = self.drive_override.velocities()
            desired = dict(desired)
            desired["target_linear"] = lin
            desired["target_angular"] = ang
            desired["source"] = "deepseek"
            desired["mode"] = "brain_drive"
            return desired
        if self.drive_override and not self.drive_override.is_active(now):
            print("[BRAIN] Drive override завершён — снова камера.")
            self.drive_override = None
        return desired

    def run(self) -> None:
        self._print_banner()
        try:
            while True:
                if not p.isConnected():
                    print("[INFO] PyBullet отключён — выход.")
                    break

                loop_start = time.time()
                self._update_scene()
                self._poll_text_commands()

                desired = self.camera.read_desired()
                desired = self._resolve_desired(desired)

                brain_out = self.safety_brain.evaluate(
                    desired["target_linear"],
                    desired["target_angular"],
                    ta=desired.get("ta", 0.0),
                    distance_z=desired.get("distance_z"),
                    tag_valid=desired.get("tag_valid", True),
                )

                tag_lost = desired.get("mode") == "tag_lost" or brain_out["status"] == "TAG_LOST"
                motor_lin, motor_ang = self.smoother.apply(
                    brain_out["final_linear"],
                    brain_out["final_angular"],
                    emergency=brain_out["override"] and not tag_lost,
                    tag_lost=tag_lost,
                )

                self.twin.set_velocity(motor_lin, motor_ang)
                x, y, yaw = self.twin.get_robot_pose()
                log_tick(self.tick, desired, brain_out, motor_lin, motor_ang, x, y, yaw)

                self.twin.step_physics(steps=PHYSICS_STEPS_PER_TICK)
                self.tick += 1

                elapsed = time.time() - loop_start
                time.sleep(max(0.0, LOOP_PERIOD - elapsed))

        except KeyboardInterrupt:
            print("\n[INFO] Остановка по Ctrl+C...")
        finally:
            if p.isConnected():
                self.twin.set_velocity(0.0, 0.0)
            print("[INFO] Отключение PyBullet...")
            self.twin.disconnect()
            print("[INFO] Foresight завершён.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Foresight unified runtime")
    parser.add_argument(
        "--text",
        help="Текстовая команда для DeepSeek / локального мозга (один раз при старте)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    runtime = ForesightRuntime(initial_text=args.text)
    runtime.run()
