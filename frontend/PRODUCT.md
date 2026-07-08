# Product

## Register

product

## Users

Hackathon jury members walking between team tables in a noisy demo hall, glancing at a
laptop or projector screen for 10-30 seconds per table, from as far as 3 meters away.
They are evaluating technical ambition and polish across dozens of projects in a short
window. They are not going to click around or read paragraphs — they need to understand
"what is this system deciding, and why" at a glance, and feel that it is real and live,
not a mockup.

Secondary user: the team member driving the demo, who triggers scenarios via preset
buttons and narrates while the dashboard does the visual work.

## Product Purpose

FORESIGHT is the dashboard face of a predictive safety layer for physical AI: a camera
(Limelight) perceives objects on a table, a PyBullet world-model simulates the outcome
of a proposed robot action via Monte-Carlo rollouts, and the system ALLOWS or BLOCKS the
action based on fall/collision risk. The dashboard visualizes perception, simulated
future, and the resulting decision in real time. Success = a judge who has never seen
the project before understands, within seconds, that this is a live safety-gating system
making real risk-based decisions — and finds it visually impressive enough to remember.
The dashboard must run flawlessly in a self-contained mock mode (no backend required)
since network/backend availability on demo day is not guaranteed.

## Brand Personality

Three words: **predictive, precise, unflinching.**

Anchor reference: SpaceX/rocket launch telemetry (Dragon/Starship mission control feeds)
— dense monospace telemetry, sharp HUD corner-bracket panels, a mostly quiet dark canvas
where color is spent only on state changes (verdict, risk), huge glanceable status text
that reads instantly from across a room. Motion should feel like live instrumentation
(sweeping gauges, counting telemetry, scanning sweeps) rather than decorative UI
transitions — every animation should read as "the system is actually thinking," not as
polish for its own sake.

## Anti-references

Not a generic SaaS admin template: no soft pastel cards, no generic dashboard widget
grid, no rounded bubbly components, no gradient-text hero metrics, no stock dashboard
color story (blue/purple gradients). Not decorative sci-fi either — every visual element
should map to a real piece of system state (a real risk number, a real object, a real
simulation count), not abstract ambient decoration.

## Design Principles

- **Glanceable over explorable.** Every panel must communicate its core fact (verdict,
  risk, object count) in under 2 seconds from 3 meters away; detail is secondary.
- **Color is a state signal, not decoration.** SAFE/CAUTION/BLOCK accent colors are
  reserved for verdict-linked state; nothing else in the UI competes for that semantic
  channel.
- **Live feeling beats static accuracy.** Counters count up, gauges sweep, trajectories
  draw in — the system should never look like a paused screenshot, even idle.
- **Mock mode is the demo.** Mock mode is not a fallback bolted on afterward; it is
  built and polished first, as if it were the only mode that will ever run, because on
  demo day it very well might be.
- **Show the mechanism, not just the verdict.** Uncertainty (sensor noise, physics
  variance), simulation count, and the active safety rule are shown alongside the
  verdict so the system reads as reasoned, not magic.

## Accessibility & Inclusion

This is a one-off live demo viewed on a shared projector/laptop, not a shipped product:
prioritize visual drama and motion over strict WCAG process (no formal
prefers-reduced-motion pass). Text contrast is still a hard requirement — the primary
reason this matters is legibility from 3 meters across a room, not compliance — so all
telemetry, verdict, and label text must hit strong contrast against the near-black
background regardless.
