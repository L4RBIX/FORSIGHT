# Kaggle LocateAnything-3B server cells

Use this as a slow semantic scan service. The local Foresight app must still work when this is offline.

## Cell 1 — install

```python
!pip install -U transformers accelerate pillow fastapi uvicorn pyngrok python-multipart
```

## Cell 2 — load model

```python
import torch
from transformers import pipeline

MODEL_ID = "nvidia/LocateAnything-3B"

pipe = pipeline(
    "image-text-to-text",
    model=MODEL_ID,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype="auto",
)
```

## Cell 3 — FastAPI app

```python
from fastapi import FastAPI, UploadFile, File, Form
from PIL import Image
import io, json, re

app = FastAPI(title="Foresight LocateAnything Server")

def _extract_text(raw):
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list) and raw:
        return _extract_text(raw[0])
    if isinstance(raw, dict):
        for key in ("generated_text", "text", "content", "answer"):
            if key in raw:
                return _extract_text(raw[key])
    return str(raw)

def normalize_locateanything_output(raw, query):
    text = _extract_text(raw)
    parsed = None
    try:
        parsed = json.loads(text)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
        if m:
            try:
                parsed = json.loads(m.group(1))
            except Exception:
                parsed = None
    detections = []
    items = []
    if isinstance(parsed, dict):
        maybe = parsed.get("detections") or parsed.get("objects") or parsed.get("boxes") or [parsed]
        items = maybe if isinstance(maybe, list) else [maybe]
    elif isinstance(parsed, list):
        items = parsed
    for obj in items:
        if not isinstance(obj, dict):
            continue
        bbox = obj.get("bbox_xyxy") or obj.get("bbox") or obj.get("box")
        point = obj.get("point_xy") or obj.get("point")
        label = str(obj.get("label") or obj.get("name") or query)
        cls = str(obj.get("class") or obj.get("class_name") or label.split()[-1])
        if bbox and len(bbox) == 4:
            bbox = [float(v) for v in bbox]
            point = point or [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
        elif point and len(point) == 2:
            point = [float(v) for v in point]
        else:
            continue
        detections.append({
            "label": label,
            "class": cls,
            "bbox_xyxy": bbox,
            "point_xy": point,
            "confidence": float(obj.get("confidence", obj.get("score", 0.75))),
            "source": "locateanything",
        })
    if detections:
        return {"ok": True, "query": query, "detections": detections, "raw": raw}
    return {"ok": False, "query": query, "detections": [], "error": "Could not parse LocateAnything output", "raw": raw}

@app.get("/health")
def health():
    return {"ok": True, "model": MODEL_ID}

@app.post("/locate")
async def locate(image: UploadFile = File(...), query: str = Form(...)):
    img = Image.open(io.BytesIO(await image.read())).convert("RGB")
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": img},
            {"type": "text", "text": query}
        ]
    }]
    raw = pipe(text=messages, max_new_tokens=512)
    return normalize_locateanything_output(raw, query)
```

## Cell 4 — tunnel

```python
from pyngrok import ngrok
import uvicorn, threading

public_url = ngrok.connect(8000).public_url
print("PUBLIC_URL:", public_url)

thread = threading.Thread(
    target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000),
    daemon=True
)
thread.start()
```

You can also run locally:

```bash
uvicorn kaggle.locateanything_server:app --host 0.0.0.0 --port 8000
```
