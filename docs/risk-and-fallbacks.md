# Risks and Fallbacks

## Limelight fails

Fallback:

- Webcam.
- Prerecorded frame.
- Mock scene.

## LocateAnything endpoint fails

Fallback:

- YOLO fallback.
- Preset object labels.

## Tracking is unstable

Fallback:

- EMA smoothing.
- Freeze last stable object pose.
- Use preset scene.

## Full pipeline breaks

Fallback:

- Mock WebSocket.
- Preset action.
- Dashboard still shows the full story.

## Demo rule

Never debug silently during judging. Switch to mock mode, explain the fallback, and continue the story.
