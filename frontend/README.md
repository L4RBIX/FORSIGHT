# FORESIGHT

**A predictive safety layer for physical AI.**

A camera (Limelight) sees a table of objects. A PyBullet world-model simulates the
consequences of a proposed robot action via Monte-Carlo rollouts, estimates a
fall/collision risk, and ALLOWS or BLOCKS the action. This is the mission-control
dashboard for that system: perception, simulated future, and the resulting verdict,
all live and glanceable from across a room.

## Running it

```bash
npm install
npm run dev
```

That's it — the dashboard boots straight into **MOCK mode**, cycling through four
scripted scenarios (SAFE, BLOCK, CAUTION, and an open-vocabulary "new object" scan) so
it looks and feels finished with zero backend. Use the preset buttons, the **Scan
Scene** button, or the free-text action field at the bottom to trigger scenarios
on demand instead of waiting for the auto-cycle.

If a backend is running a WebSocket server at `ws://localhost:8000/ws` emitting the
frame shape in [`src/types/telemetry.ts`](src/types/telemetry.ts) at ~10–15Hz, flip the
top-bar toggle to **Live** (or just leave it — the app tries Live by default and only
falls back to Mock if nothing answers). Any disconnect during a live session
auto-falls back to Mock and the badge reflects it.

## Stack

Vite + React + TypeScript + Tailwind CSS v4, Framer Motion for UI animation,
`@react-three/fiber` + `@react-three/drei` for the World Twin 3D scene. Inter and
JetBrains Mono are bundled locally via `@fontsource` — no CDN calls anywhere.

## Structure

- `src/types/telemetry.ts` — the wire contract (shared by the WebSocket client and the mock generator)
- `src/mock/` — the scripted scenarios, the scanning→predicting→verdict state machine, and the free-text action heuristic
- `src/ws/client.ts` + `src/hooks/useForesightData.ts` — the live WebSocket client and the live/mock switching logic
- `src/components/layout/` — top bar, verdict banner, bottom action bar
- `src/components/perception/` — camera view + bounding boxes + object confidence list
- `src/components/three/` — the World Twin 3D scene (table, objects, danger zone, ghost trajectories)
- `src/components/decision/` — the risk gauge and the rest of the decision readout

`PRODUCT.md` and `DESIGN.md` in this directory capture the strategic and visual design
system this UI was built against.
