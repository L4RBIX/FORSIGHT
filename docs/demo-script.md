# FORESIGHT - Live Demo Script

## Goal

Show that Foresight predicts unsafe physical consequences before the robot acts.

## Setup

Objects:

- Blue box.
- Mug.
- Table.
- AprilTag anchor.
- One unknown judge object.

Camera:

- Limelight 3A or webcam fallback.

Dashboard:

- Open fullscreen.
- WebSocket connected or mock mode active.

## Demo flow

### Step 1 - Live perception

Say: "Here is what the system sees right now. It detects the scene and builds a world model."

Show camera feed, bounding boxes, object names, and the 3D world model.

### Step 2 - Unknown object

Say: "Now I am adding an object the system was not hardcoded for."

Place object.

Say: "It names it using open-vocabulary detection. No labels, no fixed object list."

### Step 3 - Proposed action

Say: "Now we propose an action: push the blue box to the right."

Enter:

```text
push the blue box to the right
```

### Step 4 - Prediction

Show dashboard verdict:

```text
BLOCK - 87% risk
Reason: mug likely falls from table
```

Say: "The system does not just say dangerous. It explains why."

### Step 5 - Grounding explanation

Say: "Why 87? Because we measured sensor jitter on this setup and then ran 30 simulations under uncertainty. In 26 of them, the mug ended up on the floor."

Show sensor noise, sampled mass/friction, simulation count, failures, and risk.

### Step 6 - Reality check

Physically perform the action or a controlled version.

Say: "Prediction and reality match: the unsafe outcome is exactly what Foresight blocked."

### Step 7 - Judge interaction

Say: "Now you can suggest an action and we will ask Foresight before executing it."

## Emergency fallback

If live perception fails:

- Switch to mock mode.
- Say: "The live perception feed is unstable, so we are switching to the same scene replay to show the decision pipeline."
- Continue the demo.

Never silently debug during judging.
