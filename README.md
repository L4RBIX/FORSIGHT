# FORESIGHT

**Predictive safety layer for physical AI.**

Foresight lets a robot see the consequences of an action before it moves. Before a robot sends a command to its motors, Foresight builds a live world model of the scene, simulates the proposed action, estimates failure probability, and returns:

`ALLOW` or `BLOCK`.

Built for **Cursor Robotics Hackathon Almaty - World Models track - July 8, 2026**.

## One-sentence pitch

Foresight is a safety layer that lets robots predict the physical consequences of their actions one second before acting, then block dangerous actions.

## Problem

Robots are moving from isolated industrial cells into spaces shared with people: homes, warehouses, labs, kitchens, and shops.

Traditional safety is mostly based on keeping humans away from robots: fences, cages, emergency stops, and fixed zones. That breaks down when the robot is supposed to operate near fragile objects or people.

The core failure is simple:

> The robot acts first and learns the consequence later.

If a robot pushes a box and knocks over a mug, it usually discovers the failure only after the mug has already fallen.

Foresight gives the robot a way to ask:

> What will happen if I do this?

## Why now

Robot safety is becoming more urgent as robots move closer to people.

- A U.S. workplace study identified 41 robot-related fatalities between 1992 and 2017.
- A 2024 analysis of OSHA Severe Injury Reports identified 77 robot-related accidents from 2015 to 2022.
- The collaborative robot market is projected to grow from about USD 2.9B in 2025 to USD 17.2B by 2033.

This makes predictive safety more valuable than simple after-the-fact collision detection.

## First users

Foresight is a horizontal safety layer, but the first clear users are:

1. Home service robots operating near humans, hot cups, glass, food, and furniture.
2. Warehouse manipulators handling fragile goods in uncertain environments.
3. Research robotics teams that need a fast safety oracle before sending actions to hardware.

## Solution

Foresight sits between the robot planner and the motors:

```text
Robot plan -> FORESIGHT -> Motors
```

For each proposed action:

1. Perceive the scene.
2. Build a live world model.
3. Mirror objects into a physics simulator.
4. Run the action forward under uncertainty.
5. Estimate risk.
6. Return ALLOW or BLOCK.

Example:

```text
Action: push blue box right
Result: BLOCK
Risk: 87%
Reason: mug likely falls from table
Evidence: 26 / 30 simulations ended with mug on the floor
```

## Architecture

```text
Camera / Limelight 3A
        |
        v
AprilTag world anchor + object detection
        |
        v
SceneGraph
        |
        v
PyBullet digital twin
        |
        v
Monte Carlo action simulation
        |
        v
SafetyGate
        |
        v
ALLOW / BLOCK + reason
        |
        v
Dashboard
```

## Two-loop perception system

Foresight uses two perception loops.

**Fast loop** runs locally around 10-15 Hz. It handles the AprilTag world anchor, camera-to-table coordinate system, known-object tracking, position smoothing, and continuous SceneGraph updates.

**Slow loop** runs on demand. It handles open-vocabulary object discovery, names unknown objects, adds them to the scene, and can call LocateAnything-3B through a remote inference endpoint.

This split matters because heavy open-vocabulary models are too slow for every frame, but useful when a new unknown object appears.

## Physical grounding

Foresight is not just an LLM wrapper.

The system grounds decisions in physical measurements:

1. Real sensor input: Limelight 3A camera, AprilTag anchor, measured pose jitter.
2. Physical simulation: PyBullet digital twin, object geometry approximations, table, edges, collision zones.
3. Uncertainty propagation: sensor noise, unknown mass, unknown friction, localization error.
4. Monte Carlo risk: repeated simulations with varied physical parameters.

Example:

```text
Measured sensor jitter: +/-4.0 mm, +/-1.8 deg
Unknown object mass: sampled from range
Simulations: 30
Failures: 26
Risk: 87%
Decision: BLOCK
```

The jitter values must be measured on the actual demo setup before presenting.

## Demo flow

1. System shows the live camera view.
2. Foresight detects and names objects.
3. A judge places an unknown object.
4. The system names it using open-vocabulary detection.
5. User proposes an action: `push the blue box to the right`.
6. Foresight simulates the action.
7. Dashboard shows risk percentage, predicted trajectory, reason for block, and uncertainty parameters.
8. System returns: `BLOCK - 87% risk that the mug falls`.
9. Team performs the action physically.
10. Prediction is compared with reality.

## Dashboard

The frontend is a mission-control dashboard designed to be readable from 3 meters.

Main panels:

- Verdict banner: SAFE, CAUTION, BLOCK
- Camera panel with detected objects
- 3D world model
- Ghost trajectories of predicted futures
- Risk gauge
- Safety reason
- Uncertainty panel
- Action input
- Preset demo actions

The dashboard supports two modes:

- MOCK mode: works without backend.
- LIVE mode: connects to the backend WebSocket.

## Tech stack

Hardware:

- Limelight 3A
- AprilTag 36h11
- Optional webcam fallback

Backend:

- Python
- FastAPI
- WebSocket
- PyBullet
- OpenCV
- YOLO fallback
- LocateAnything-3B remote inference
- LLM API for natural-language action parsing

Frontend:

- React
- Vite
- TypeScript
- Tailwind CSS
- Framer Motion
- react-three-fiber

## Repository layout

```text
backend/     Python perception, simulation, safety gate, API
frontend/    React dashboard
docs/        Project description, architecture, demo script
slides/      HTML pitch deck
demo/        Mock scenes and preset actions
media/       Screenshots and demo assets
```

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Mock demo

```bash
cd demo
bash run_mock_demo.sh
```

## Environment variables

Create `.env` from `.env.example`.

```env
CLAUDE_API_KEY=
LOCATEANYTHING_ENDPOINT=
LIMELIGHT_HOST=
USE_MOCK=false
RISK_BLOCK_THRESHOLD=0.30
```

## API overview

WebSocket:

```text
ws://localhost:8000/ws
ws://localhost:8000/ws/scene
```

Example message:

```json
{
  "timestamp": 1720000000,
  "mode": "live",
  "scene": {
    "objects": [
      {
        "id": "box_2",
        "label": "blue box",
        "position": [0.32, 0.11, 0.04],
        "confidence": 0.91
      }
    ]
  },
  "risk": {
    "decision": "BLOCK",
    "risk_percent": 87,
    "reason": "Mug likely falls from table",
    "simulations": 30,
    "failures": 26
  }
}
```

## Safety rule

Default rule:

```text
BLOCK if predicted failure risk > 30%
```

Failure events:

- Object falls from table.
- Collision with protected object.
- Collision with human zone.
- Object enters unsafe region.
- Simulator uncertainty is too high.

## Hackathon scope

What works today:

- Live or mock scene stream.
- Object detection pipeline.
- SceneGraph.
- Physics-based action prediction.
- Monte Carlo risk estimate.
- Safety decision.
- Dashboard visualization.
- Demo presets.

What is next:

- Connect to a real robot arm.
- Improve object geometry estimation.
- Calibrate mass/friction online.
- Support multi-step action planning.
- Deploy as a ROS2 safety node.

## Team

Team Foresight

- Kydyrbek Bekarys - perception / calibration
- Mukanov Arsen - simulation / safety oracle
- Kasymov Ali - dashboard / agent / pitch

## Final message

Any robot that interacts with the physical world needs to see the future before it acts.

Foresight is that layer.
