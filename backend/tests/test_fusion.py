from foresight.perception.fake_perception import FakePerceptionProvider
from foresight.perception.fusion import SceneFusion
from foresight.schemas import Detection2D


def test_fusion_keeps_apriltag_priority_no_duplicate_box():
    scene = FakePerceptionProvider().get_scene()
    det = Detection2D(label="blue box", class_name="box", color="blue", bbox_xyxy=(1,2,3,4), confidence=0.9, source="yolo")
    fused = SceneFusion().fuse(scene, [det], None)
    assert len([o for o in fused.objects if o.class_name == "box" and o.color == "blue"]) == 1


def test_fusion_uses_detection_when_no_apriltag():
    det = Detection2D(label="cup", class_name="mug", bbox_xyxy=(100,100,160,180), confidence=0.8, source="locateanything")
    fused = SceneFusion().fuse(None, None, [det])
    assert fused.objects
    assert fused.workspace.x_min < fused.workspace.x_max
