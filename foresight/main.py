from __future__ import annotations

from pathlib import Path

from foresight.config import CONFIG, AppConfig
from foresight.parser.command_parser import parse_command
from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.perception.fusion import SceneFusion
from foresight.perception.locateanything_client import LocateAnythingClient
from foresight.planning.action_planner import plan_action
from foresight.robot.executor import DryRunExecutor
from foresight.safety.safety_gate import SafetyGate
from foresight.schemas import Detection2D, FullPipelineResult, RobotExecutionResult, SceneGraph
from foresight.simulation.oracle import ConsequenceOracle


class ForesightPipeline:
    def __init__(self, perception_provider: object | None = None, config: AppConfig = CONFIG, fast_mode: bool = True):
        self.config = config
        self.perception_provider = perception_provider or FakePerceptionProvider()
        self.oracle = ConsequenceOracle(config=config, fast_mode=fast_mode)
        self.safety_gate = SafetyGate(config=config)
        self.executor = DryRunExecutor()
        self._last_scene: SceneGraph | None = None

    def get_scene(self) -> SceneGraph:
        scene = self.perception_provider.get_scene()  # type: ignore[attr-defined]
        self._last_scene = scene
        return scene

    def _store_locate_detections(self, detections: list[Detection2D]) -> bool:
        setter = getattr(self.perception_provider, "set_locate_detections", None)
        if callable(setter):
            setter(detections)
            return True
        attr_name = "latest_locate_detections"
        try:
            if hasattr(self.perception_provider, attr_name):
                setattr(self.perception_provider, attr_name, list(detections))
                return True
        except Exception:
            return False
        return False

    def _fuse_transient_locate(self, base_scene: SceneGraph, detections: list[Detection2D]) -> SceneGraph:
        # Compatibility path for simple providers such as FakePerceptionProvider.
        # Real AI perception should use FusionPerceptionProvider so detections are retained.
        fused = SceneFusion().fuse(base_scene, None, detections)
        fused.warnings.append("LocateAnything detections were fused transiently; use FusionPerceptionProvider to retain them across frames")
        return fused

    def scan_scene_semantic(self, image_path: Path, query: str) -> SceneGraph:
        if not self.config.enable_locateanything:
            scene = self.get_scene()
            scene.warnings.append("LocateAnything disabled by config; semantic scan skipped")
            return scene

        result = LocateAnythingClient(self.config).scan_image(image_path, query)
        stored = False
        if result.ok:
            stored = self._store_locate_detections(result.detections)

        scene = self.get_scene()
        if not result.ok:
            scene.warnings.append(f"LocateAnything scan failed: {result.error}")
            return scene

        if stored:
            scene.warnings.append(f"LocateAnything fused {len(result.detections)} semantic detections into the SceneGraph")
            return scene

        if result.detections:
            scene = self._fuse_transient_locate(scene, result.detections)
            scene.warnings.append(f"LocateAnything fused {len(result.detections)} semantic detections into a transient SceneGraph")
        else:
            scene.warnings.append("LocateAnything returned no detections")
        self._last_scene = scene
        return scene

    def evaluate_command(self, command: str) -> FullPipelineResult:
        scene = self.get_scene()
        parsed = parse_command(command)
        planning = plan_action(parsed, scene)
        simulation = None
        skill = planning.skill
        if planning.ok and skill is not None and skill.simulation_required:
            simulation = self.oracle.predict(scene, skill)
        safety = self.safety_gate.decide(scene, skill, simulation) if planning.ok else self.safety_gate.decide(scene, None, None)
        return FullPipelineResult(command=command, scene=scene, parsed=parsed, planning=planning, simulation=simulation, safety=safety, robot_skill=skill)

    def execute_if_safe(self, result: FullPipelineResult) -> RobotExecutionResult:
        if result.robot_skill is None:
            return RobotExecutionResult(sent=False, reason="No robot skill available")
        return self.executor.execute(result.safety, result.robot_skill)
