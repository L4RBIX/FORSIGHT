# Foresight PM — Physical World Model Safety Demo

Foresight mirrors a tabletop scene from perception, plans high-level robot skills,
predicts action consequences, and blocks risky actions before any robot executor is
called.

The hard rule is simple: **this is not an LLM wrapper.** The parser proposes an
intent; the scene graph, planner, Monte Carlo oracle, and safety gate decide
whether the action is allowed.

## Current status

Implemented modules:

- Offline fake `SceneGraph` demo.
- Deterministic English/Russian/Kazakh command parser.
- Action planner with target/reference/edge grounding.
- PyBullet live-twin adapter with graceful no-PyBullet fallback.
- Monte Carlo consequence oracle with uncertainty-aware approximate physics.
- Safety gate that blocks forbidden targets, high force/distance, missing simulation, and high-risk outcomes.
- Limelight AprilTag JSON adapter with anchor transform and fake fallback.
- Kaggle LocateAnything server notebook and local client.
- Optional YOLO/ByteTrack tracker wrapper.
- Fusion and homography projection modules.
- Safe dry-run/HTTP/serial robot executors.
- CLI and optional Streamlit operator console.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`pybullet`, `ultralytics`, `streamlit`, and `pyserial` are optional for the core
fake demo. The code runs without them, but installing them unlocks the GUI twin,
YOLO tracker, web UI, and serial bridge.

## Run tests

```bash
pytest -q
```

## 60-second offline demo

```bash
python -m foresight.ui.demo_cli --fake --pybullet-direct
```

Expected flow:

1. Scene objects print: blue box, red box, mug near edge.
2. Parser output prints for `push the blue box toward the mug`.
3. Planner produces a `RobotSkillRequest` with target, reference, direction, distance, and force.
4. Oracle predicts fall/collision/boundary risk.
5. Safety gate returns allowed/blocked.
6. Result is logged to `runs/demo_log.jsonl`.

Try safer edge command:

```bash
python -m foresight.ui.demo_cli --fake --command "push the mug away from edge"
```

## Limelight mode

```bash
export LIMELIGHT_RESULTS_URL="http://172.29.0.1:5807/results"
python -m foresight.ui.demo_cli --limelight
```

If Limelight is unavailable, `LIMELIGHT_FAKE_ON_ERROR=true` keeps the demo alive
with the fake scene and adds a warning.

## Kaggle LocateAnything semantic scan

1. Open `kaggle/kaggle_notebook_cells.md` in Kaggle.
2. Run the install/model/server/tunnel cells.
3. Copy the printed ngrok URL.
4. Run:

```bash
python -m foresight.ui.demo_cli --fake --kaggle-url "https://YOUR.ngrok-free.app"
```

LocateAnything is treated as a slow semantic scan, not the fast tracking loop.
Core execution still requires calibrated projection/fusion and safety approval.

## YOLO fallback

```bash
export ENABLE_YOLO=true
export YOLO_MODEL=yolo26n.pt
```

The wrapper uses Ultralytics tracking with ByteTrack when available. If weights or
Ultralytics are missing, it returns an empty detection list and the app falls back
to AprilTags/fake scene.

## Robot bridge contract

Executors accept only high-level skill JSON after the safety gate returns
`READY_FOR_EXECUTOR`:

```json
{
  "skill_type": "push",
  "target_object_id": "obj_blue_box",
  "direction_vector_world": [1, 0, 0],
  "distance_m": 0.1,
  "force_n": 4.0
}
```

No executor receives raw PWM, torque, joint velocity, or motor power from the
parser/LLM. Unsafe decisions are never sent.

## AI perception fusion provider

The integrated perception path is `FusionPerceptionProvider`:

```python
from foresight.perception.fusion_provider import FusionPerceptionProvider
from foresight.perception.frame_source import MjpegFrameSource
from foresight.perception.limelight_client import LimelightPerceptionProvider
from foresight.main import ForesightPipeline

provider = FusionPerceptionProvider(
    apriltag_provider=LimelightPerceptionProvider(),
    frame_source=MjpegFrameSource("http://172.29.0.1:5800/stream.mjpg"),
)
pipeline = ForesightPipeline(perception_provider=provider)
```

Flow:

1. Limelight AprilTags provide trusted 3D objects and anchor/workspace.
2. A frame source provides camera frames for YOLO.
3. YOLO detections are projected to the table plane and fused into `SceneGraph`.
4. `pipeline.scan_scene_semantic(image_path, query)` stores LocateAnything detections in the provider; the next fused scene includes them as tentative low-confidence objects.
5. Fusion deduplicates by tracker ID first, then nearest world position, then class/color only as a weak fallback against trusted 3D objects. Multiple same-class/same-color detections are preserved when positions differ.

If only AprilTag 0 is visible, the fused scene keeps `world_frame="table_anchor"`, workspace bounds, and uncertainty from Limelight instead of falling back to a fake workspace.
