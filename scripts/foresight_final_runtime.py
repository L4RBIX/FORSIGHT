
from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import requests

try:
    import pybullet as p
    import pybullet_data
except Exception as e:
    raise RuntimeError("pybullet is required. Install with: pip install pybullet") from e


# =========================
# DATA MODELS
# =========================

@dataclass
class Obj:
    id: str
    label: str
    class_name: str
    color: str
    pos: list[float]       # [x,y,z] meters, table frame
    size: list[float]      # [x,y,z] meters
    mass: float
    movable: bool = True
    source: str = "fake"
    confidence: float = 1.0


@dataclass
class Action:
    action: str
    target_id: str | None
    direction: list[float]
    force_n: float
    distance_m: float


@dataclass
class Event:
    type: str
    object_id: str | None
    severity: str
    message: str
    t: float


@dataclass
class OracleResult:
    verdict: str
    risk: float
    fall_probability: float
    collision_probability: float
    boundary_probability: float
    simulations: int
    events: list[dict[str, Any]]
    reason: str
    action: dict[str, Any]
    objects: list[dict[str, Any]]
    trajectories: dict[str, list[list[float]]]


TABLE_X_MIN = -0.55
TABLE_X_MAX = 0.55
TABLE_Y_MIN = -0.35
TABLE_Y_MAX = 0.35
TABLE_Z = 0.0

DEFAULT_TAG_OBJECT_MAP = {
    1: {"id": "blue_box", "label": "blue box", "class_name": "box", "color": "blue", "size": [0.09, 0.09, 0.09], "mass": 0.18},
    2: {"id": "red_box", "label": "red box", "class_name": "box", "color": "red", "size": [0.09, 0.09, 0.09], "mass": 0.18},
    3: {"id": "bottle", "label": "bottle", "class_name": "bottle", "color": "white", "size": [0.055, 0.055, 0.18], "mass": 0.12},
    4: {"id": "mug", "label": "mug", "class_name": "mug", "color": "white", "size": [0.08, 0.08, 0.10], "mass": 0.18},
}


# =========================
# PARSER
# =========================

def norm(v: list[float]) -> list[float]:
    a = np.array(v, dtype=float)
    n = float(np.linalg.norm(a))
    if n < 1e-9:
        return [1.0, 0.0, 0.0]
    return (a / n).tolist()


def parse_command(command: str, objects: list[Obj]) -> Action:
    text = command.lower().replace("ё", "е")

    force_n = 4.0
    distance_m = 0.12

    # Distance parsing
    import re
    m_cm = re.search(r"(\d+(?:\.\d+)?)\s*(cm|см)", text)
    m_m = re.search(r"(\d+(?:\.\d+)?)\s*(m|м)", text)
    if m_cm:
        distance_m = float(m_cm.group(1)) / 100.0
    elif m_m:
        distance_m = float(m_m.group(1))

    m_force = re.search(r"(\d+(?:\.\d+)?)\s*(n|н)", text)
    if m_force:
        force_n = float(m_force.group(1))

    # Target selection
    target = None

    def contains_any(words):
        return any(w in text for w in words)

    for obj in objects:
        if obj.id.lower() in text or obj.label.lower() in text:
            target = obj
            break

    if target is None:
        for obj in objects:
            if obj.color and obj.color.lower() in text:
                if obj.class_name in text or obj.label.split()[-1] in text:
                    target = obj
                    break

    if target is None:
        if contains_any(["blue", "син", "көк", "синю"]):
            candidates = [o for o in objects if o.color == "blue"]
            target = candidates[0] if candidates else None
        elif contains_any(["red", "крас", "қызыл"]):
            candidates = [o for o in objects if o.color == "red"]
            target = candidates[0] if candidates else None
        elif contains_any(["bottle", "бутыл", "бөтел"]):
            candidates = [o for o in objects if o.class_name == "bottle"]
            target = candidates[0] if candidates else None
        elif contains_any(["mug", "cup", "круж", "чаш"]):
            candidates = [o for o in objects if o.class_name in {"mug", "cup"}]
            target = candidates[0] if candidates else None
        elif objects:
            # demo fallback
            target = objects[0]

    # Direction
    direction = [1.0, 0.0, 0.0]
    if contains_any(["left", "налево", "солға", "лев"]):
        direction = [-1.0, 0.0, 0.0]
    elif contains_any(["right", "вправо", "оңға", "прав"]):
        direction = [1.0, 0.0, 0.0]
    elif contains_any(["forward", "вперед", "алға"]):
        direction = [0.0, 1.0, 0.0]
    elif contains_any(["back", "назад", "артқа"]):
        direction = [0.0, -1.0, 0.0]

    # Toward mug / bottle / reference
    if contains_any(["toward", "towards", "к ", "қарай", "ближе"]):
        refs = []
        if contains_any(["mug", "cup", "круж", "чаш"]):
            refs = [o for o in objects if o.class_name in {"mug", "cup"}]
        elif contains_any(["bottle", "бутыл", "бөтел"]):
            refs = [o for o in objects if o.class_name == "bottle"]

        if target is not None and refs:
            ref = refs[0]
            direction = norm([ref.pos[0] - target.pos[0], ref.pos[1] - target.pos[1], 0.0])

    # Away from edge: go toward table center
    if contains_any(["away from edge", "от края", "шетінен", "края"]):
        if target:
            direction = norm([-target.pos[0], -target.pos[1], 0.0])

    return Action(
        action="push",
        target_id=target.id if target else None,
        direction=norm(direction),
        force_n=max(0.5, min(force_n, 8.0)),
        distance_m=max(0.02, min(distance_m, 0.40)),
    )


# =========================
# LIMELIGHT
# =========================

def read_limelight_scene(url: str, timeout: float = 0.5) -> list[Obj]:
    """
    Reads Limelight /results JSON.
    Important: this works only on the local laptop connected to Limelight,
    not from Kaggle cloud.
    """
    data = requests.get(url, timeout=timeout).json()
    results = data.get("Results", data)
    fiducials = results.get("Fiducial", [])

    objects: list[Obj] = []

    for f in fiducials:
        fid = int(f.get("fID", -1))
        if fid not in DEFAULT_TAG_OBJECT_MAP:
            continue

        pose = f.get("t6t_cs") or f.get("t6t_rs") or []
        if len(pose) < 3:
            continue

        spec = DEFAULT_TAG_OBJECT_MAP[fid]

        # Fast practical mapping for demo:
        # Limelight camera space -> approximate table coordinates.
        # You should calibrate later; for hackathon demo this gives live motion.
        x_cam = float(pose[0])
        z_cam = float(pose[2])

        x = max(TABLE_X_MIN, min(TABLE_X_MAX, x_cam))
        y = max(TABLE_Y_MIN, min(TABLE_Y_MAX, z_cam - 0.75))

        size = spec["size"]
        obj_z = size[2] / 2.0

        objects.append(Obj(
            id=spec["id"],
            label=spec["label"],
            class_name=spec["class_name"],
            color=spec["color"],
            pos=[x, y, obj_z],
            size=size,
            mass=spec["mass"],
            source="limelight_apriltag",
            confidence=float(f.get("ta", 0.01)) if f.get("ta") is not None else 0.9,
        ))

    return objects


def fake_scene() -> list[Obj]:
    return [
        Obj("blue_box", "blue box", "box", "blue", [-0.25, 0.00, 0.045], [0.09, 0.09, 0.09], 0.18, source="fake"),
        Obj("bottle", "bottle", "bottle", "white", [0.18, 0.02, 0.09], [0.055, 0.055, 0.18], 0.12, source="fake"),
        Obj("mug", "mug", "mug", "white", [0.43, 0.05, 0.05], [0.08, 0.08, 0.10], 0.18, source="fake"),
    ]


# =========================
# PYBULLET ORACLE
# =========================

def shape_for_obj(obj: Obj):
    sx, sy, sz = obj.size
    if obj.class_name == "bottle":
        return p.createCollisionShape(p.GEOM_CYLINDER, radius=max(sx, sy) / 2.0, height=sz)
    if obj.class_name in {"mug", "cup"}:
        return p.createCollisionShape(p.GEOM_CYLINDER, radius=max(sx, sy) / 2.0, height=sz)
    return p.createCollisionShape(p.GEOM_BOX, halfExtents=[sx / 2, sy / 2, sz / 2])


def build_world(objects: list[Obj], gui: bool = False):
    cid = p.connect(p.GUI if gui else p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(1 / 240)

    # Table as fixed box
    table_col = p.createCollisionShape(
        p.GEOM_BOX,
        halfExtents=[(TABLE_X_MAX - TABLE_X_MIN) / 2, (TABLE_Y_MAX - TABLE_Y_MIN) / 2, 0.02],
    )
    table_vis = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[(TABLE_X_MAX - TABLE_X_MIN) / 2, (TABLE_Y_MAX - TABLE_Y_MIN) / 2, 0.02],
        rgbaColor=[0.45, 0.35, 0.25, 1],
    )
    table_id = p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=table_col,
        baseVisualShapeIndex=table_vis,
        basePosition=[0, 0, -0.02],
    )

    body_by_obj: dict[str, int] = {}

    for obj in objects:
        col = shape_for_obj(obj)
        color = [0.2, 0.2, 1, 1] if obj.color == "blue" else [1, 0.2, 0.2, 1] if obj.color == "red" else [0.9, 0.9, 0.9, 1]
        vis = p.createVisualShape(
            p.GEOM_BOX if obj.class_name == "box" else p.GEOM_CYLINDER,
            halfExtents=[obj.size[0] / 2, obj.size[1] / 2, obj.size[2] / 2] if obj.class_name == "box" else None,
            radius=max(obj.size[0], obj.size[1]) / 2 if obj.class_name != "box" else None,
            length=obj.size[2] if obj.class_name != "box" else None,
            rgbaColor=color,
        )
        bid = p.createMultiBody(
            baseMass=obj.mass if obj.movable else 0,
            baseCollisionShapeIndex=col,
            baseVisualShapeIndex=vis,
            basePosition=obj.pos,
        )
        p.changeDynamics(bid, -1, lateralFriction=0.55, rollingFriction=0.02, spinningFriction=0.02)
        body_by_obj[obj.id] = bid

    return cid, table_id, body_by_obj


def get_obj_by_id(objects: list[Obj], oid: str | None) -> Obj | None:
    if oid is None:
        return None
    for o in objects:
        if o.id == oid:
            return o
    return None


def run_one_sim(objects: list[Obj], action: Action, sim_seconds: float = 4.0, gui: bool = False) -> tuple[list[Event], dict[str, list[list[float]]]]:
    cid, table_id, bodies = build_world(objects, gui=gui)

    events: list[Event] = []
    trajectories: dict[str, list[list[float]]] = {o.id: [] for o in objects}

    target_obj = get_obj_by_id(objects, action.target_id)
    if target_obj is None or action.target_id not in bodies:
        p.disconnect(cid)
        return [Event("NO_TARGET", None, "high", "Target object was not found", 0.0)], trajectories

    target_body = bodies[action.target_id]
    direction = np.array(action.direction, dtype=float)
    direction = direction / (np.linalg.norm(direction) + 1e-9)

    # Controlled virtual robot push.
    # Instead of one tiny impulse, we push until planned distance is reached.
    # This makes commands like "push mug right 30 cm" actually test boundary/fall risk.
    start_pos = np.array(p.getBasePositionAndOrientation(target_body)[0], dtype=float)
    push_speed = max(0.12, min(0.85, action.force_n * 0.12))
    max_push_steps = int(max(0.15, action.distance_m / push_speed) * 240)

    seen_collision_pairs = set()
    steps = int(sim_seconds * 240)

    for step in range(steps):
        if step < max_push_steps:
            cur_pos = np.array(p.getBasePositionAndOrientation(target_body)[0], dtype=float)
            traveled = float(np.linalg.norm((cur_pos - start_pos)[:2]))

            if traveled < action.distance_m:
                p.resetBaseVelocity(
                    target_body,
                    linearVelocity=(direction * push_speed).tolist(),
                    angularVelocity=[0.0, 0.0, 0.0],
                )
            else:
                p.resetBaseVelocity(
                    target_body,
                    linearVelocity=[0.0, 0.0, 0.0],
                    angularVelocity=[0.0, 0.0, 0.0],
                )

        p.stepSimulation()
        t = step / 240.0

        # trajectories
        for obj in objects:
            bid = bodies[obj.id]
            pos, _orn = p.getBasePositionAndOrientation(bid)
            trajectories[obj.id].append([float(pos[0]), float(pos[1]), float(pos[2])])

            # fall / boundary
            sx, sy, sz = obj.size
            if pos[2] < -0.05:
                if not any(e.type == "FALL" and e.object_id == obj.id for e in events):
                    events.append(Event("FALL", obj.id, "critical", f"{obj.label} fell below table", t))

            if pos[0] < TABLE_X_MIN - sx or pos[0] > TABLE_X_MAX + sx or pos[1] < TABLE_Y_MIN - sy or pos[1] > TABLE_Y_MAX + sy:
                if not any(e.type == "BOUNDARY_EXIT" and e.object_id == obj.id for e in events):
                    events.append(Event("BOUNDARY_EXIT", obj.id, "high", f"{obj.label} left table bounds", t))

            # tipping bottle/mug: if roll/pitch too high
            _pos, orn = p.getBasePositionAndOrientation(bid)
            roll, pitch, _yaw = p.getEulerFromQuaternion(orn)
            if obj.class_name in {"bottle", "mug", "cup"} and (abs(roll) > 0.75 or abs(pitch) > 0.75):
                if not any(e.type == "TIP_OVER" and e.object_id == obj.id for e in events):
                    events.append(Event("TIP_OVER", obj.id, "critical", f"{obj.label} tipped over", t))

        # collisions between movable objects
        for i, a in enumerate(objects):
            for b in objects[i + 1:]:
                pts = p.getContactPoints(bodies[a.id], bodies[b.id])
                if pts:
                    pair = tuple(sorted([a.id, b.id]))
                    if pair not in seen_collision_pairs:
                        seen_collision_pairs.add(pair)
                        events.append(Event("COLLISION", f"{pair[0]}:{pair[1]}", "medium", f"{pair[0]} collided with {pair[1]}", t))

    p.disconnect(cid)
    return events, trajectories


def jitter_objects(objects: list[Obj], sigma_pos: float = 0.004, mass_jitter: float = 0.35) -> list[Obj]:
    out = []
    for o in objects:
        pos = [
            o.pos[0] + random.gauss(0, sigma_pos),
            o.pos[1] + random.gauss(0, sigma_pos),
            o.pos[2],
        ]
        mass = max(0.03, o.mass * random.uniform(1 - mass_jitter, 1 + mass_jitter))
        out.append(Obj(o.id, o.label, o.class_name, o.color, pos, list(o.size), mass, o.movable, o.source, o.confidence))
    return out


def predict(objects: list[Obj], action: Action, n: int = 30, gui: bool = False) -> OracleResult:
    all_events: list[Event] = []
    fall_count = 0
    collision_count = 0
    boundary_count = 0
    sample_trajectories: dict[str, list[list[float]]] = {}

    for i in range(n):
        sim_objects = jitter_objects(objects)
        events, traj = run_one_sim(sim_objects, action, gui=(gui and i == 0))
        all_events.extend(events)

        if any(e.type in {"FALL", "TIP_OVER"} for e in events):
            fall_count += 1
        if any(e.type == "COLLISION" for e in events):
            collision_count += 1
        if any(e.type == "BOUNDARY_EXIT" for e in events):
            boundary_count += 1

        if i == 0:
            # downsample for JSON
            sample_trajectories = {
                k: v[::24] for k, v in traj.items()
            }

    fall_p = fall_count / n
    col_p = collision_count / n
    bound_p = boundary_count / n
    risk = max(fall_p, col_p * 0.6, bound_p)

    if risk >= 0.30:
        verdict = "BLOCK"
    elif risk >= 0.15:
        verdict = "CAUTION"
    else:
        verdict = "SAFE"

    reason = f"{fall_count}/{n} fall/tip, {collision_count}/{n} collision, {boundary_count}/{n} boundary exit"

    return OracleResult(
        verdict=verdict,
        risk=round(risk, 3),
        fall_probability=round(fall_p, 3),
        collision_probability=round(col_p, 3),
        boundary_probability=round(bound_p, 3),
        simulations=n,
        events=[asdict(e) for e in all_events[:80]],
        reason=reason,
        action=asdict(action),
        objects=[asdict(o) for o in objects],
        trajectories=sample_trajectories,
    )


def load_scene(use_limelight: bool, limelight_url: str | None) -> list[Obj]:
    if use_limelight and limelight_url:
        try:
            objs = read_limelight_scene(limelight_url)
            if objs:
                print(f"✅ Limelight objects: {len(objs)}")
                return objs
            print("⚠️ Limelight connected but no mapped AprilTag objects found. Using fake scene.")
        except Exception as e:
            print("⚠️ Limelight failed:", repr(e))
            print("Using fake scene.")

    return fake_scene()


# =========================
# FASTAPI SERVER
# =========================


def make_app():
    from fastapi import FastAPI, Body

    app = FastAPI(title="Foresight Final Runtime")

    @app.get("/health")
    def health():
        return {"ok": True, "service": "foresight-final-runtime"}

    @app.post("/evaluate")
    def evaluate(req = Body(...)):
        """
        Accepts JSON body:
        {
          "command": "push the mug right 30 cm",
          "simulations": 20,
          "use_limelight": false,
          "limelight_url": null
        }
        """
        if not isinstance(req, dict):
            req = {}

        command = str(req.get("command", "push the blue box toward the mug"))
        simulations = int(req.get("simulations", 30))
        simulations = max(1, min(simulations, 80))

        use_limelight = bool(req.get("use_limelight", False))
        limelight_url = req.get("limelight_url", None)

        try:
            objects_payload = req.get("objects", None)

            if isinstance(objects_payload, list) and len(objects_payload) > 0:
                objects = []
                for item in objects_payload:
                    try:
                        objects.append(Obj(
                            id=str(item.get("id", item.get("label", "object"))),
                            label=str(item.get("label", item.get("id", "object"))),
                            class_name=str(item.get("class_name", item.get("class", "object"))),
                            color=str(item.get("color", "unknown")),
                            pos=[float(x) for x in item.get("pos", [0.0, 0.0, 0.05])],
                            size=[float(x) for x in item.get("size", [0.08, 0.08, 0.08])],
                            mass=float(item.get("mass", 0.15)),
                            movable=bool(item.get("movable", True)),
                            source=str(item.get("source", "yolo")),
                            confidence=float(item.get("confidence", 0.8)),
                        ))
                    except Exception:
                        continue

                if not objects:
                    objects = load_scene(use_limelight, limelight_url)
            else:
                objects = load_scene(use_limelight, limelight_url)

            action = parse_command(command, objects)
            result = predict(objects, action, n=simulations)
            return asdict(result)

        except Exception as e:
            return {
                "verdict": "ERROR",
                "risk": 1.0,
                "fall_probability": 0.0,
                "collision_probability": 0.0,
                "boundary_probability": 0.0,
                "simulations": simulations,
                "events": [
                    {
                        "type": "RUNTIME_ERROR",
                        "object_id": None,
                        "severity": "critical",
                        "message": repr(e),
                        "t": 0.0
                    }
                ],
                "reason": "Runtime error: " + repr(e),
                "action": {},
                "objects": [],
                "trajectories": {}
            }

    @app.get("/scene")
    def scene(use_limelight: bool = False, limelight_url: str | None = None):
        try:
            objects = load_scene(use_limelight, limelight_url)
            return {"objects": [asdict(o) for o in objects]}
        except Exception as e:
            return {"objects": [], "error": repr(e)}

    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--command", default="push the blue box toward the mug")
    ap.add_argument("--simulations", type=int, default=30)
    ap.add_argument("--limelight", action="store_true")
    ap.add_argument("--limelight-url", default=os.getenv("LIMELIGHT_RESULTS_URL", "http://172.29.0.1:5807/results"))
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--gui", action="store_true")
    args = ap.parse_args()

    if args.serve:
        import uvicorn
        app = make_app()
        print(f"✅ Serving Foresight runtime on http://0.0.0.0:{args.port}")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
        return

    objects = load_scene(args.limelight, args.limelight_url)
    action = parse_command(args.command, objects)
    result = predict(objects, action, n=args.simulations, gui=args.gui)

    out = asdict(result)

    print("\n================ FORESIGHT FINAL RESULT ================")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("========================================================\n")

    os.makedirs("runs", exist_ok=True)
    path = "runs/final_oracle_log.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print("✅ saved:", path)


if __name__ == "__main__":
    main()
