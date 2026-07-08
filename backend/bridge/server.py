"""
FORESIGHT backend bridge: Limelight -> your PyBullet sim -> WebSocket, matching
the contract the dashboard expects at ws://localhost:8000/ws.

Run:
    pip install -r requirements.txt
    python server.py

Then open the dashboard — it tries Live by default and connects automatically.
If you forced Mock earlier, flip the top-bar toggle back to Live.
"""
from __future__ import annotations

import asyncio
import json
import logging

import websockets

from limelight_client import LimelightClient
from state import ForesightState

log = logging.getLogger("foresight-server")

HOST = "localhost"
PORT = 8000


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    limelight = LimelightClient()
    limelight.start()

    clients: set = set()

    def broadcast(frame) -> None:
        if not clients:
            return
        payload = json.dumps(frame.to_dict())
        websockets.broadcast(clients, payload)

    state = ForesightState(limelight, on_frame=broadcast)
    perception_task = asyncio.create_task(state.run_forever())

    async def handler(ws) -> None:
        clients.add(ws)
        log.info("Dashboard connected (%d client(s))", len(clients))
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except ValueError:
                    log.warning("Ignoring malformed message: %r", raw)
                    continue

                msg_type = msg.get("type")
                if msg_type == "scan":
                    asyncio.create_task(state.handle_scan())
                elif msg_type == "propose_action":
                    asyncio.create_task(state.handle_propose_action(msg.get("text", "")))
                else:
                    log.warning("Unknown command type: %r", msg_type)
        finally:
            clients.discard(ws)
            log.info("Dashboard disconnected (%d client(s))", len(clients))

    try:
        async with websockets.serve(handler, HOST, PORT):
            log.info("FORESIGHT backend listening on ws://%s:%d/ws", HOST, PORT)
            await perception_task
    finally:
        limelight.stop()


if __name__ == "__main__":
    asyncio.run(main())
