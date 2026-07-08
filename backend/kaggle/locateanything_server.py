from __future__ import annotations

import json
import re
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from PIL import Image

MODEL_ID = "nvidia/LocateAnything-3B"
app = FastAPI(title="Foresight LocateAnything Server")
pipe = None


def _extract_text(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list) and raw:
        return _extract_text(raw[0])
    if isinstance(raw, dict):
        for key in ("generated_text", "text", "content", "answer"):
            if key in raw:
                return _extract_text(raw[key])
    return str(raw)


def _json_from_text(text: str) -> Any | None:
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            return None
    return None


def _detection_from_obj(obj: dict[str, Any], query: str) -> dict[str, Any] | None:
    bbox = obj.get("bbox_xyxy") or obj.get("bbox") or obj.get("box")
    point = obj.get("point_xy") or obj.get("point")
    label = str(obj.get("label") or obj.get("name") or query)
    cls = str(obj.get("class") or obj.get("class_name") or label.split()[-1] if label else "object")
    if bbox and len(bbox) == 4:
        bbox = [float(v) for v in bbox]
        point = point or [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
    elif point and len(point) == 2:
        point = [float(v) for v in point]
    else:
        return None
    return {
        "label": label,
        "class": cls,
        "bbox_xyxy": bbox,
        "point_xy": point,
        "confidence": float(obj.get("confidence", obj.get("score", 0.75))),
        "source": "locateanything",
    }


def normalize_locateanything_output(raw: Any, query: str) -> dict[str, Any]:
    text = _extract_text(raw)
    parsed = _json_from_text(text)
    detections: list[dict[str, Any]] = []
    candidates: list[Any] = []
    if isinstance(parsed, dict):
        maybe = parsed.get("detections") or parsed.get("objects") or parsed.get("boxes") or [parsed]
        candidates = maybe if isinstance(maybe, list) else [maybe]
    elif isinstance(parsed, list):
        candidates = parsed

    for item in candidates:
        if isinstance(item, dict):
            det = _detection_from_obj(item, query)
            if det:
                detections.append(det)

    if not detections:
        # Fallback: parse bracketed boxes in text, e.g. [100,120,220,260]
        for m in re.finditer(r"\[(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\]", text):
            x1, y1, x2, y2 = map(float, m.groups())
            detections.append({
                "label": query,
                "class": "object",
                "bbox_xyxy": [x1, y1, x2, y2],
                "point_xy": [(x1+x2)/2, (y1+y2)/2],
                "confidence": 0.60,
                "source": "locateanything",
            })
    if detections:
        return {"ok": True, "query": query, "detections": detections, "raw": raw}
    return {"ok": False, "query": query, "detections": [], "error": "Could not parse LocateAnything output", "raw": raw}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "model": MODEL_ID, "loaded": pipe is not None}


@app.post("/locate")
async def locate(image: UploadFile = File(...), query: str = Form(...)) -> dict[str, Any]:
    import io

    if pipe is None:
        return {"ok": False, "query": query, "detections": [], "error": "Model pipeline is not loaded", "raw": None}
    img = Image.open(io.BytesIO(await image.read())).convert("RGB")
    messages = [{"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": query}]}]
    raw = pipe(text=messages, max_new_tokens=512)
    return normalize_locateanything_output(raw, query)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
