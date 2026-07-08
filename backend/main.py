from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from foresight.api.routes import router
from foresight.api.websocket import ws_router

app = FastAPI(
    title="Foresight Backend",
    description="Predictive world-model safety layer for physical AI.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(ws_router)


@app.get("/")
def root():
    return {
        "name": "Foresight",
        "status": "running",
        "description": "Predictive safety layer for physical AI robots.",
    }
