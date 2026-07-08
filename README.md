# Foresight Logic

## 1. Scene Perception

The perception pipeline begins with the robot camera (Limelight 3A or a standard webcam). Every incoming frame is processed by a lightweight local perception stack.

YOLO performs real-time object detection for known classes such as bottles, cups and other common objects. Since COCO models do not reliably detect cardboard boxes, a dedicated color-based tracker detects blue and red boxes used during the demonstration.

Each detected object is converted into a normalized scene representation containing:

- Object ID
- Class
- Color
- Confidence
- Estimated size
- Estimated mass
- 3D position on the table
- Motion state

Pixel coordinates are projected into table coordinates using a calibrated mapping so every object exists in a common world coordinate system.

---

## 2. Scene Representation

All detected objects are merged into a single Scene Graph.

Each object contains semantic and physical properties:

```json
{
    "id": "blue_box",
    "class": "box",
    "color": "blue",
    "position": [x, y, z],
    "size": [sx, sy, sz],
    "mass": 0.18,
    "movable": true,
    "confidence": 0.92
}
```

This Scene Graph represents the current physical state of the environment.

---

## 3. Natural Language Planning

Robot commands are written in natural language.

Example:

```
Push the blue box toward the mug.
```

The command parser converts this instruction into a structured robot action.

Example:

```json
{
    "target": "blue_box",
    "direction": [1,0,0],
    "distance": 0.30,
    "force": 4.0
}
```

No robot motion is executed at this stage.

---

## 4. Digital Twin Generation

The Scene Graph is copied into PyBullet.

For every object the simulator creates a physical body using:

- collision geometry
- visual geometry
- estimated dimensions
- estimated mass
- gravity
- friction

The resulting simulation becomes a live digital twin of the observed environment.

---

## 5. Action Simulation

Instead of executing the command immediately, the requested action is first executed inside the digital twin.

The simulator predicts approximately four seconds of future motion.

During simulation the system continuously monitors:

- collisions
- tipping
- falling objects
- objects leaving the table
- unsafe interactions

The robot itself never performs the action until prediction is finished.

---

## 6. Monte Carlo World Model

Real sensors are noisy.

To account for uncertainty, the simulator repeats the same action many times.

Each simulation slightly perturbs:

- object position
- friction
- object mass
- initial motion

Typical execution:

```
30 simulations
```

Example outcome:

```
Simulation 1  -> safe
Simulation 2  -> bottle falls
Simulation 3  -> collision
...
Simulation 30 -> safe
```

This produces a probabilistic prediction rather than a single deterministic answer.

---

## 7. Event Detection

Every simulation generates physical events.

Supported event types include:

- COLLISION
- FALL
- TIP_OVER
- BOUNDARY_EXIT

Each event stores:

- timestamp
- involved objects
- severity
- event type

---

## 8. Risk Estimation

After all simulations finish, event statistics are aggregated.

Example:

```
30 simulations

24 safe
4 collisions
2 bottle falls
```

The system computes:

- collision probability
- fall probability
- boundary exit probability
- overall risk score

---

## 9. Safety Decision

A rule-based safety layer evaluates the computed risk.

Decision states:

```
SAFE
```

Action may be executed.

```
CAUTION
```

Action is risky but still observable.

```
BLOCK
```

Action is rejected because predicted consequences exceed the safety threshold.

The decision is based on predicted physical outcomes, not on the language model.

---

## 10. Robot Interface

The runtime exposes a REST API.

```
POST /evaluate
```

Input:

```json
{
    "command": "Push the blue box toward the mug.",
    "objects": [...],
    "simulations": 30
}
```

Output:

```json
{
    "verdict": "BLOCK",
    "risk": 0.87,
    "collision_probability": 0.23,
    "fall_probability": 0.71,
    "boundary_probability": 0.66,
    "events": [...]
}
```

The virtual robot reads only the returned verdict.

```
SAFE
    ↓
Execute action

BLOCK
    ↓
Reject action
```

---

## 11. Complete Pipeline

```
Camera (Limelight 3A / Webcam)
            │
            ▼
      YOLO Detection
            │
            ▼
     Color Box Tracker
            │
            ▼
       Scene Graph
            │
            ▼
 Natural Language Parser
            │
            ▼
     Action Generation
            │
            ▼
     PyBullet Digital Twin
            │
            ▼
   Monte Carlo Simulation
            │
            ▼
 Physical Event Detection
            │
            ▼
      Risk Estimation
            │
            ▼
   SAFE / CAUTION / BLOCK
            │
            ▼
 Virtual Robot Execution
```

## Design Principle

The language model never directly controls the robot.

Artificial intelligence is used only for perception and command interpretation.

The final decision is always produced by the physics-based world model after predicting the future consequences of the requested action.
