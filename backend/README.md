# Foresight Backend

Python backend for the Foresight predictive safety layer.

It exposes:

- `GET /api/health`
- `GET /api/scene`
- `POST /api/simulate`
- `WS /ws/scene`

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend defaults to mock mode so the dashboard can run without robot hardware.

## Legacy and experimental modules

- `foresight/` contains the original perception, planning, simulation, and safety implementation.
- `bridge/` contains the WebSocket bridge from the dashboard archive.
- `experimental/` contains the PyBullet runtime files from the PYBULLET archive.
- `assets/models/yolo26n.pt` is the local YOLO model artifact from the demo bundle.
