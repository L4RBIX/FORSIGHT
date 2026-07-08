from __future__ import annotations

import argparse
import json
from pathlib import Path

from foresight.config import CONFIG
from foresight.main import ForesightPipeline
from foresight.perception.fake_perception import FakePerceptionProvider


def _provider_from_args(args: argparse.Namespace):
    if args.limelight:
        from foresight.perception.limelight_client import LimelightPerceptionProvider

        return LimelightPerceptionProvider()
    return FakePerceptionProvider()


def _log_result(result) -> None:
    path = CONFIG.run_log_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(result.model_dump_json() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Foresight tabletop world-model demo CLI")
    parser.add_argument("--fake", action="store_true", help="Use deterministic fake scene")
    parser.add_argument("--limelight", action="store_true", help="Use Limelight AprilTag adapter")
    parser.add_argument("--kaggle-url", help="Enable LocateAnything URL for semantic scan", default=None)
    parser.add_argument("--pybullet-gui", action="store_true", help="Open PyBullet GUI if pybullet is installed")
    parser.add_argument("--pybullet-direct", action="store_true", help="Use PyBullet DIRECT if installed")
    parser.add_argument("--command", default="push the blue box toward the mug")
    args = parser.parse_args()

    if args.kaggle_url:
        CONFIG.locateanything_url = args.kaggle_url.rstrip("/")
        CONFIG.enable_locateanything = True

    pipeline = ForesightPipeline(perception_provider=_provider_from_args(args), fast_mode=True)
    scene = pipeline.get_scene()
    print("\n=== Scene objects ===")
    for obj in scene.objects:
        print(f"- {obj.id}: {obj.label} class={obj.class_name} color={obj.color} pose=({obj.pose.x:.2f},{obj.pose.y:.2f},{obj.pose.z:.2f}) conf={obj.confidence:.2f} source={obj.source}")
    if scene.warnings:
        print("Warnings:", "; ".join(scene.warnings))

    command = args.command
    result = pipeline.evaluate_command(command)
    _log_result(result)

    print(f"\n=== Parser output for: {command!r} ===")
    print(json.dumps(result.parsed.model_dump(by_alias=True), indent=2, ensure_ascii=False))
    print("\n=== Planned skill request ===")
    print(json.dumps(result.robot_skill.model_dump() if result.robot_skill else None, indent=2, ensure_ascii=False))
    print("\n=== Simulation outcome ===")
    print(json.dumps(result.simulation.model_dump() if result.simulation else None, indent=2, ensure_ascii=False))
    print("\n=== Safety decision ===")
    print(json.dumps(result.safety.model_dump(), indent=2, ensure_ascii=False))
    print(f"\nLogged to {Path(CONFIG.run_log_path)}")

    if args.pybullet_gui or args.pybullet_direct:
        from foresight.simulation.pybullet_twin import PyBulletTwin

        twin = PyBulletTwin(gui=args.pybullet_gui)
        twin.load_scene(result.scene)
        print(f"PyBullet available: {twin.available}")
        twin.disconnect()


if __name__ == "__main__":
    main()
