
from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any

import cv2
import numpy as np
import requests


TABLE_X_MIN = -0.55
TABLE_X_MAX = 0.55
TABLE_Y_MIN = -0.35
TABLE_Y_MAX = 0.35


def pixel_to_table(px: float, py: float, w: int, h: int) -> list[float]:
    """
    Fast demo projection.
    Maps image pixel bottom-center to approximate table coordinates.
    Better calibration can replace this later.
    """
    x = (px / max(w, 1) - 0.5) * (TABLE_X_MAX - TABLE_X_MIN)
    y = (0.5 - py / max(h, 1)) * (TABLE_Y_MAX - TABLE_Y_MIN)
    return [float(x), float(y)]


def make_obj(
    obj_id: str,
    label: str,
    class_name: str,
    color: str,
    bbox: list[int],
    frame_w: int,
    frame_h: int,
    confidence: float,
    source: str,
) -> dict[str, Any]:
    x1, y1, x2, y2 = bbox
    px = (x1 + x2) / 2
    py = y2

    x, y = pixel_to_table(px, py, frame_w, frame_h)

    if class_name == "bottle":
        size = [0.055, 0.055, 0.18]
        mass = 0.12
        z = size[2] / 2
    elif class_name in {"mug", "cup"}:
        size = [0.08, 0.08, 0.10]
        mass = 0.18
        z = size[2] / 2
        class_name = "mug"
    else:
        size = [0.09, 0.09, 0.09]
        mass = 0.18
        z = size[2] / 2

    return {
        "id": obj_id,
        "label": label,
        "class_name": class_name,
        "color": color,
        "pos": [x, y, z],
        "size": size,
        "mass": mass,
        "movable": True,
        "source": source,
        "confidence": float(confidence),
        "bbox_xyxy": bbox,
    }


def detect_colored_boxes(frame: np.ndarray) -> list[dict[str, Any]]:
    """
    YOLO COCO does not reliably have 'box' class.
    So for demo we detect blue/red boxes by color.
    """
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    detections = []

    color_ranges = {
        "blue": [
            (np.array([90, 60, 40]), np.array([135, 255, 255])),
        ],
        "red": [
            (np.array([0, 70, 40]), np.array([10, 255, 255])),
            (np.array([170, 70, 40]), np.array([180, 255, 255])),
        ],
    }

    for color, ranges in color_ranges.items():
        mask = None

        for low, high in ranges:
            part = cv2.inRange(hsv, low, high)
            mask = part if mask is None else cv2.bitwise_or(mask, part)

        mask = cv2.medianBlur(mask, 5)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_area = 0

        for c in contours:
            area = cv2.contourArea(c)
            if area < 700:
                continue

            x, y, bw, bh = cv2.boundingRect(c)

            if bw < 20 or bh < 20:
                continue

            if area > best_area:
                best_area = area
                best = [x, y, x + bw, y + bh]

        if best is not None:
            obj_id = f"{color}_box"
            detections.append(make_obj(
                obj_id=obj_id,
                label=f"{color} box",
                class_name="box",
                color=color,
                bbox=best,
                frame_w=w,
                frame_h=h,
                confidence=0.82,
                source="color_tracker",
            ))

    return detections


def detect_yolo_objects(frame: np.ndarray, model) -> list[dict[str, Any]]:
    h, w = frame.shape[:2]
    detections = []

    results = model.track(frame, persist=True, verbose=False)

    if not results:
        return detections

    r = results[0]

    if r.boxes is None:
        return detections

    names = r.names

    for box in r.boxes:
        cls_id = int(box.cls[0].item())
        label = names.get(cls_id, str(cls_id)).lower()
        conf = float(box.conf[0].item())

        if conf < 0.35:
            continue

        if label not in {"bottle", "cup"}:
            continue

        xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
        track_id = None

        if getattr(box, "id", None) is not None and box.id is not None:
            try:
                track_id = int(box.id[0].item())
            except Exception:
                track_id = None

        class_name = "bottle" if label == "bottle" else "mug"
        obj_id = f"{class_name}_{track_id}" if track_id is not None else class_name

        detections.append(make_obj(
            obj_id=obj_id,
            label=class_name,
            class_name=class_name,
            color="white",
            bbox=xyxy,
            frame_w=w,
            frame_h=h,
            confidence=conf,
            source="yolo",
        ))

    return detections


def dedupe_objects(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Keep color boxes and YOLO objects.
    If duplicates have same id, keep higher confidence.
    """
    by_id = {}

    for obj in objects:
        oid = obj["id"]

        if oid not in by_id:
            by_id[oid] = obj
        else:
            if obj.get("confidence", 0) > by_id[oid].get("confidence", 0):
                by_id[oid] = obj

    return list(by_id.values())


def draw_objects(frame: np.ndarray, objects: list[dict[str, Any]], verdict: str | None = None, risk: float | None = None):
    out = frame.copy()

    for obj in objects:
        bbox = obj.get("bbox_xyxy")
        if not bbox:
            continue

        x1, y1, x2, y2 = [int(x) for x in bbox]

        color = (255, 0, 0) if obj.get("color") == "blue" else (0, 0, 255) if obj.get("color") == "red" else (0, 255, 255)

        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        txt = f"{obj['id']} {obj.get('confidence', 0):.2f}"
        cv2.putText(out, txt, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        pos = obj.get("pos", [0, 0, 0])
        ptxt = f"x={pos[0]:.2f} y={pos[1]:.2f}"
        cv2.putText(out, ptxt, (x1, y2 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    if verdict is not None:
        banner = f"FORESIGHT: {verdict} risk={risk}"
        cv2.rectangle(out, (0, 0), (out.shape[1], 42), (0, 0, 0), -1)

        bcolor = (0, 0, 255) if verdict == "BLOCK" else (0, 255, 255) if verdict == "CAUTION" else (0, 255, 0)
        cv2.putText(out, banner, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.85, bcolor, 2)

    return out


def open_video_source(source: str):
    if source.isdigit():
        return cv2.VideoCapture(int(source))
    return cv2.VideoCapture(source)


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--source", default=os.getenv("VIDEO_SOURCE", "0"),
                    help="0 for webcam, or Limelight MJPEG URL like http://172.29.0.1:5800")
    ap.add_argument("--runtime-url", default=os.getenv("FORESIGHT_RUNTIME_URL", "http://127.0.0.1:8765"))
    ap.add_argument("--command", default="push the mug right 30 cm")
    ap.add_argument("--simulations", type=int, default=20)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--robot-url", default=os.getenv("ROBOT_URL", ""))

    args = ap.parse_args()

    print("Loading YOLO...")
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")

    cap = open_video_source(args.source)

    if not cap.isOpened():
        print("❌ Could not open video source:", args.source)
        print("Try --source 0 for webcam, or check Limelight stream URL.")
        return

    last_eval_time = 0
    last_result = None

    while True:
        ok, frame = cap.read()

        if not ok or frame is None:
            print("⚠️ No frame")
            time.sleep(0.1)
            continue

        color_objs = detect_colored_boxes(frame)
        yolo_objs = detect_yolo_objects(frame, model)
        objects = dedupe_objects(color_objs + yolo_objs)

        now = time.time()

        # Evaluate at most once per second, or immediately in --once mode.
        should_eval = args.once or (now - last_eval_time > 1.0)

        if should_eval:
            last_eval_time = now

            payload = {
                "command": args.command,
                "simulations": args.simulations,
                "use_limelight": False,
                "objects": objects,
            }

            try:
                r = requests.post(args.runtime_url.rstrip("/") + "/evaluate", json=payload, timeout=30)
                data = r.json()
                last_result = data

                verdict = data.get("verdict", "ERROR")
                risk = data.get("risk", 1.0)
                reason = data.get("reason", "")

                print("\n================ FORESIGHT ================")
                print("objects:", [o["id"] for o in objects])
                print("command:", args.command)
                print("verdict:", verdict, "risk:", risk)
                print("reason:", reason)
                print("events:", data.get("events", [])[:5])

                robot_command = {
                    "execute": verdict != "BLOCK",
                    "verdict": verdict,
                    "risk": risk,
                    "reason": reason,
                    "action": data.get("action", {}),
                    "objects": objects,
                }

                print("robot_command:", json.dumps(robot_command, ensure_ascii=False))

                # Optional: send to virtual robot server/site
                if args.robot_url:
                    try:
                        rr = requests.post(args.robot_url.rstrip("/") + "/robot_action", json=robot_command, timeout=5)
                        print("robot_url status:", rr.status_code)
                    except Exception as e:
                        print("robot_url failed:", repr(e))

            except Exception as e:
                print("❌ Runtime request failed:", repr(e))

            if args.once:
                break

        verdict = None
        risk = None

        if isinstance(last_result, dict):
            verdict = last_result.get("verdict")
            risk = last_result.get("risk")

        if args.show:
            vis = draw_objects(frame, objects, verdict, risk)
            cv2.imshow("Foresight YOLO + Robot Bridge", vis)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
