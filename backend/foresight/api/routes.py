import time

from fastapi import APIRouter

from foresight.config import settings
from foresight.decision.safety_gate import SafetyGate
from foresight.world_model.scene_graph import SceneGraph, SceneObject

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {
        "ok": True,
        "service": "foresight-backend",
        "mode": "mock" if settings.use_mock else "live",
    }


@router.get("/scene")
def get_scene():
    return SceneGraph(
        timestamp=time.time(),
        mode="mock" if settings.use_mock else "live",
        objects=[
            SceneObject(
                id="box_2",
                label="blue box",
                object_class="box",
                position=[0.32, 0.11, 0.04],
                size=[0.16, 0.12, 0.08],
                confidence=0.91,
                source="mock",
            ),
            SceneObject(
                id="mug_1",
                label="white mug",
                object_class="mug",
                position=[0.56, 0.12, 0.05],
                size=[0.08, 0.08, 0.10],
                confidence=0.88,
                source="mock",
            ),
        ],
    )


@router.post("/simulate")
def simulate_action():
    gate = SafetyGate(block_threshold=settings.risk_block_threshold)
    return gate.decide(
        failures=26,
        simulations=settings.monte_carlo_runs,
        reason="Mug likely falls from table",
    )
