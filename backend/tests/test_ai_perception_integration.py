from pathlib import Path
from unittest.mock import patch

from foresight.config import AppConfig
from foresight.main import ForesightPipeline
from foresight.perception.fusion import SceneFusion
from foresight.perception.fusion_provider import FusionPerceptionProvider
from foresight.perception.frame_source import FakeFrameSource
from foresight.schemas import Detection2D, LocateAnythingResult, SceneGraph, SensorUncertainty, WorkspaceBounds


class DummyYolo:
    def __init__(self, detections=None, exc=None):
        self.detections = detections or []
        self.exc = exc

    def track_frame(self, frame):
        if self.exc:
            raise self.exc
        return self.detections


class DummyApriltagProvider:
    def __init__(self, scene=None, exc=None):
        self.scene = scene
        self.exc = exc

    def get_scene(self):
        if self.exc:
            raise self.exc
        return self.scene


def anchor_only_scene() -> SceneGraph:
    return SceneGraph(
        timestamp_s=1.0,
        world_frame="table_anchor",
        objects=[],
        workspace=WorkspaceBounds(x_min=-0.2, x_max=0.2, y_min=-0.1, y_max=0.1, z_min=0, z_max=0.4),
        uncertainty=SensorUncertainty(position_std_m=0.004, rotation_std_deg=1.5),
        warnings=["anchor only"],
    )


def test_fusion_provider_yolo_to_scene():
    det = Detection2D(label="cup", class_name="cup", bbox_xyxy=(300, 220, 340, 280), confidence=0.8, source="yolo", track_id=10)
    provider = FusionPerceptionProvider(frame_source=FakeFrameSource(), yolo_tracker=DummyYolo([det]), use_fake_when_empty=False)

    scene = provider.get_scene()

    assert any(obj.id == "det_yolo_track_10" for obj in scene.objects)
    assert any(obj.class_name == "cup" for obj in scene.objects)


def test_locateanything_scan_adds_object_to_scene(tmp_path: Path):
    cfg = AppConfig(enable_locateanything=True)
    provider = FusionPerceptionProvider(frame_source=FakeFrameSource(), yolo_tracker=DummyYolo([]), use_fake_when_empty=False)
    pipeline = ForesightPipeline(perception_provider=provider, config=cfg, fast_mode=True)
    image = tmp_path / "scene.jpg"
    image.write_bytes(b"not a real image; client is mocked")
    det = Detection2D(label="green bottle", class_name="bottle", color="green", bbox_xyxy=(420, 180, 470, 310), confidence=0.76, source="locateanything")

    class Client:
        def __init__(self, config):
            self.config = config

        def scan_image(self, image_path, query):
            return LocateAnythingResult(ok=True, query=query, detections=[det])

    with patch("foresight.main.LocateAnythingClient", Client):
        scene = pipeline.scan_scene_semantic(image, "find the green bottle")

    assert any(obj.class_name == "bottle" and obj.color == "green" for obj in scene.objects)
    assert any("LocateAnything fused" in warning for warning in scene.warnings)


def test_anchor_only_scene_keeps_table_frame():
    provider = FusionPerceptionProvider(
        apriltag_provider=DummyApriltagProvider(anchor_only_scene()),
        frame_source=FakeFrameSource(),
        yolo_tracker=DummyYolo([]),
        use_fake_when_empty=True,
    )

    scene = provider.get_scene()

    assert scene.world_frame == "table_anchor"
    assert scene.workspace.x_min == -0.2
    assert scene.objects == []
    assert any("anchor" in warning.lower() for warning in scene.warnings)


def test_two_blue_boxes_are_not_deduped():
    det1 = Detection2D(label="blue box", class_name="box", color="blue", bbox_xyxy=(100, 100, 150, 170), confidence=0.9, source="yolo")
    det2 = Detection2D(label="blue box", class_name="box", color="blue", bbox_xyxy=(480, 100, 530, 170), confidence=0.9, source="yolo")

    scene = SceneFusion().fuse(None, [det1, det2], None)

    blue_boxes = [obj for obj in scene.objects if obj.class_name == "box" and obj.color == "blue"]
    assert len(blue_boxes) == 2
    assert blue_boxes[0].id != blue_boxes[1].id


def test_provider_survives_yolo_failure():
    provider = FusionPerceptionProvider(frame_source=FakeFrameSource(), yolo_tracker=DummyYolo(exc=RuntimeError("boom")))

    scene = provider.get_scene()

    assert scene.objects
    assert any("YOLO tracker failed" in warning for warning in scene.warnings)


def test_provider_survives_limelight_failure():
    det = Detection2D(label="mug", class_name="mug", bbox_xyxy=(300, 220, 340, 280), confidence=0.8, source="yolo")
    provider = FusionPerceptionProvider(
        apriltag_provider=DummyApriltagProvider(exc=RuntimeError("limelight down")),
        frame_source=FakeFrameSource(),
        yolo_tracker=DummyYolo([det]),
        use_fake_when_empty=False,
    )

    scene = provider.get_scene()

    assert any(obj.class_name == "mug" for obj in scene.objects)
    assert any("AprilTag/Limelight source failed" in warning for warning in scene.warnings)
