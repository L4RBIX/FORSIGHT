# FORESIGHT - Architecture

## High-level architecture

```text
[Robot Planner / Human Command]
              |
              v
        [Action Parser]
              |
              v
        [Safety Pipeline]
              |
              v
┌──────────────────────────────────────┐
│ Perception                           │
│ - Limelight 3A                       │
│ - AprilTag anchor                    │
│ - YOLO tracker                       │
│ - LocateAnything open-vocab scan     │
└──────────────────────────────────────┘
              |
              v
┌──────────────────────────────────────┐
│ SceneGraph                           │
│ - object ids                         │
│ - positions                          │
│ - labels                             │
│ - uncertainties                      │
└──────────────────────────────────────┘
              |
              v
┌──────────────────────────────────────┐
│ PyBullet Digital Twin                │
│ - geometry                           │
│ - mass/friction ranges               │
│ - table and edge zones               │
└──────────────────────────────────────┘
              |
              v
┌──────────────────────────────────────┐
│ Monte Carlo Oracle                   │
│ - repeated futures                   │
│ - failure event detection            │
│ - risk probability                   │
└──────────────────────────────────────┘
              |
              v
        [SafetyGate]
              |
              v
      ALLOW / CAUTION / BLOCK
```

## Backend

`backend/main.py` exposes the FastAPI application. The demo API is intentionally mock-first, so the frontend can show the complete flow without hardware.

## Frontend

`frontend/` is a React/Vite mission-control dashboard. It starts in live mode, attempts WebSocket connection, and falls back to mock telemetry when the backend is unavailable.

## Experimental runtime

`backend/experimental/` contains the PyBullet + Limelight + language-agent runtime files from the live demo bundle.
