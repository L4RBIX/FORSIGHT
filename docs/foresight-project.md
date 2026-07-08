# FORESIGHT - Full Project Description

Cursor Robotics Hackathon - Almaty - July 8, 2026

## Core idea

Foresight is a predictive safety layer for embodied AI. It lets a robot evaluate the likely physical consequences of a proposed action before the robot acts.

The system builds a live world model, mirrors the real scene into a physics simulator, runs the proposed action forward under uncertainty, and returns a safety decision.

Output:

```text
ALLOW / BLOCK
Risk percentage
Reason
Simulation evidence
```

Example:

```text
Action: push blue box right
Risk: 87%
Decision: BLOCK
Reason: mug likely falls from table
Evidence: 26 of 30 simulations caused failure
```

## Track fit

Track: World Models

The project directly matches:

- Simulator for robot action consequences.
- Object motion trajectory prediction.
- Spatial reasoning for navigation and manipulation.
- Physical grounding for AI agents.

## Target users

1. Home service robot builders.
2. Warehouse automation teams handling fragile goods.
3. Robotics research teams testing manipulation policies.
4. Embodied AI teams that need a safety layer before hardware execution.

## System overview

```text
Natural language / robot planner
        |
        v
Action parser
        |
        v
Foresight safety layer
        |
        v
Scene perception
        |
        v
World model
        |
        v
Physics simulation
        |
        v
Monte Carlo risk estimate
        |
        v
Safety gate
        |
        v
ALLOW / BLOCK
```

## What works now

- World-model concept.
- Perception integration.
- Simulated object consequences.
- Monte Carlo risk.
- Safety decision.
- Dashboard.
- Live demo flow.

## What comes next

- Deploy as a safety node on a real robot arm.
- Support ROS2.
- Add better object geometry.
- Learn mass and friction from interaction.
- Support multi-step action plans.
