from foresight.perception.yolo_tracker import YoloTracker


def test_yolo_unavailable_graceful():
    tracker = YoloTracker()
    assert tracker.track_frame(object()) == []
