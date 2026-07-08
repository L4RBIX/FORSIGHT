from pathlib import Path
from unittest.mock import patch

from foresight.perception.locateanything_client import LocateAnythingClient


class Resp:
    ok = True
    status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return {"ok": True, "query": "find", "detections": [{"label": "blue box", "class": "box", "bbox_xyxy": [1,2,3,4], "point_xy": [2,3], "confidence": 0.8, "source": "locateanything"}]}


def test_success(tmp_path: Path):
    img = tmp_path / "x.jpg"
    img.write_bytes(b"fake")
    with patch("requests.post", return_value=Resp()):
        result = LocateAnythingClient(base_url="http://x").scan_image(img, "find")
    assert result.ok
    assert result.detections[0].class_name == "box"


def test_timeout(tmp_path: Path):
    img = tmp_path / "x.jpg"
    img.write_bytes(b"fake")
    with patch("requests.post", side_effect=TimeoutError("boom")):
        result = LocateAnythingClient(base_url="http://x").scan_image(img, "find")
    assert not result.ok


def test_missing_file():
    result = LocateAnythingClient(base_url="http://x").scan_image("/nope.jpg", "find")
    assert not result.ok
