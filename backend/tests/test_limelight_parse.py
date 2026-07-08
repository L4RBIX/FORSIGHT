from unittest.mock import patch

from foresight.perception.limelight_client import LimelightPerceptionProvider


FIXTURE = {
    "Results": {
        "Fiducial": [
            {"fID": 0, "t6t_cs": [1, 0, 0, 0, 0, 0], "tx": 0, "ty": 0, "ta": 1},
            {"fID": 1, "t6t_cs": [1.1, 0.0, 0.04, 0, 0, 0], "tx": 0, "ty": 0, "ta": 1},
            {"fID": 2, "t6t_cs": [0.9, 0.0, 0.04, 0, 0, 0], "tx": 0, "ty": 0, "ta": 1},
        ]
    }
}


class Resp:
    def raise_for_status(self):
        return None

    def json(self):
        return FIXTURE


def test_limelight_objects_and_anchor_transform():
    with patch("requests.get", return_value=Resp()):
        scene = LimelightPerceptionProvider().get_scene()
    ids = {obj.id for obj in scene.objects}
    assert "obj_blue_box" in ids
    assert "obj_red_box" in ids
    blue = next(o for o in scene.objects if o.id == "obj_blue_box")
    assert abs(blue.pose.x - 0.1) < 1e-6
    assert scene.world_frame == "table_anchor"


def test_missing_anchor_degraded_not_crash():
    class RespNoAnchor(Resp):
        def json(self):
            return {"Results": {"Fiducial": [{"fID": 1, "t6t_cs": [1.1, 0.0, 0.04, 0, 0, 0]}]}}

    with patch("requests.get", return_value=RespNoAnchor()):
        scene = LimelightPerceptionProvider().get_scene()
    assert scene.world_frame == "camera"
    assert scene.warnings
