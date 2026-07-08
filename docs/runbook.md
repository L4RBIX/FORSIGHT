# Foresight Demo Runbook

## 1. Offline fake demo

```bash
pytest -q
python -m foresight.ui.demo_cli --fake --pybullet-direct
```

Say to judges:

> This is not an LLM wrapper. The parser proposes; the world model tests. We
> measured or configured sensor uncertainty and use Monte Carlo to compute risk.

## 2. Limelight demo

```bash
export LIMELIGHT_RESULTS_URL="http://172.29.0.1:5807/results"
python -m foresight.ui.demo_cli --limelight --pybullet-direct
```

The adapter expects tag 0 as table anchor and tags 1/2/3 as blue box, red box,
and mug unless `TAG_OBJECT_MAP_JSON` overrides the map.

## 3. Kaggle LocateAnything demo

Run `kaggle/kaggle_notebook_cells.md`, copy `PUBLIC_URL`, then:

```bash
python -m foresight.ui.demo_cli --fake --kaggle-url "https://YOUR.ngrok-free.app"
```

Use it only for slow semantic scans. Do not send every frame.

## 4. Failure modes

- Limelight unavailable → fake scene/webcam fallback; CLI warning remains visible.
- Kaggle unavailable → AprilTags/YOLO/fake scene only; core demo still works.
- PyBullet GUI fails → run `--pybullet-direct` and present printed verdict.
- Internet unavailable → no semantic scan; parser/planner/oracle/safety still work.
- YOLO weights missing → tracker returns empty detections and app continues.

## 5. Judge script

1. Ask judge for a command.
2. Show parsed intent JSON.
3. Show scene objects and uncertainty.
4. Show planned skill.
5. Show Monte Carlo risk.
6. Show final safety decision.
7. Only dry-run executor is used unless a real robot bridge is explicitly configured.

## 6. Freeze time

Do not add new features in the final 30 minutes. Use fallback commands:

- `scan scene`
- `push the blue box right`
- `push the blue box toward the mug`
- `push the mug away from edge`
