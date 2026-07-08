# FORESIGHT backend bridge

Limelight 3/3A (neural detector) → your PyBullet sim → WebSocket → the dashboard.

```
backend/
  contract.py           # mirrors src/types/telemetry.ts exactly — the wire contract
  limelight_client.py    # Limelight ingestion: HTTP /results (detections) + MJPEG stream (camera_frame)
  sim_adapter.py          # <-- wire your existing PyBullet sim in here
  state.py                # scanning -> predicting -> live state machine (mirrors src/mock/mockEngine.ts)
  server.py                # WebSocket entrypoint, ws://localhost:8000/ws
```

## Run it

```bash
cd backend
pip install -r requirements.txt
python server.py
```

Leave the dashboard's top-bar toggle on **Live** (it's the default and connects
automatically). The badge flips to `LIVE` once the first frame arrives; if the
server isn't running, it silently sits on `MOCK` and keeps retrying every 4s.

## The two things you actually need to change

**1. `sim_adapter.py` — plug in your PyBullet sim.** Everything else already
matches the contract; `run_simulation(objects, action)` is the one function the
server calls, and it must return a `Prediction` (risk, verdict, outcome, reason,
n_sims, trajectories, safety_rule). Shipped with a rough heuristic placeholder so
the whole pipeline is runnable before you've wired anything in — replace its
body with a call into your existing module.

**2. `limelight_client.py` — confirm the detection field names.** Limelight's
`/results` JSON schema has shifted slightly across LL OS releases. If
`get_detections()` comes back empty with your neural pipeline actively running,
run:

```bash
python limelight_client.py
```

That prints the raw payload from `http://limelight.local:5807/results` so you
can see your firmware's actual keys and adjust `_parse_detections` /
`_bbox_from_det` to match. Also update `LimelightConfig.host` in that file if
you're not on mDNS (`limelight.local`) — use the camera's IP instead.

**Object position placeholder:** `tx`/`ty`/`ta` (angular offset + target area)
get converted to a rough table-plane position with a placeholder scale factor
— replace that with real geometry from your camera's mount height/angle if you
want the World Twin's object positions to be accurate rather than approximate.

## Command protocol (dashboard → backend)

The dashboard sends these over the same socket whenever you click a preset
button, hit **Scan Scene**, or submit the free-text action field — see
`src/types/commands.ts` on the frontend side:

```json
{ "type": "scan" }
{ "type": "propose_action", "text": "push blue box right" }
```

`state.py` handles both: `scan` re-reads the Limelight and returns to `live`
with no prediction; `propose_action` re-scans, matches the mentioned object by
label, calls `sim_adapter.run_simulation`, and emits the result.

## Not using NetworkTables

This intentionally talks to the Limelight over plain HTTP (`/results` for
detections, `/stream.mjpg` for video) rather than NetworkTables, so it runs
standalone on a laptop at a demo table with no roboRIO or NT server involved.
If you're already running this on an FRC robot with NetworkTables live, you can
swap `LimelightClient.get_detections()` for an NT read instead — the rest of
the pipeline doesn't care where `DetectedObject`s come from.
