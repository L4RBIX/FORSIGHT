<!-- SEED: derived directly from the founder's design brief + one confirmed visual-anchor
     answer (SpaceX/rocket telemetry). Re-run `/impeccable document` once the UI is built
     to capture the real, as-shipped tokens. -->
---
name: FORESIGHT
description: A predictive safety layer for physical AI — mission-control HUD for perception, simulated futures, and verdicts.
colors:
  void-black: "#0a0e14"
  panel-surface: "#0d131c"
  panel-border: "#1c2530"
  hairline: "rgba(255,255,255,0.08)"
  grid-line: "rgba(255,255,255,0.035)"
  safe: "#00e08a"
  caution: "#ffb020"
  block: "#ff3b47"
  text-primary: "#eef2f7"
  text-secondary: "#8b96a8"
  text-tertiary: "#5b6472"
typography:
  display:
    fontFamily: "Inter, -apple-system, sans-serif"
    fontSize: "clamp(3rem, 7vw, 5.5rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Inter, -apple-system, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  label:
    fontFamily: "Inter, -apple-system, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.12em"
  body:
    fontFamily: "Inter, -apple-system, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.4
  telemetry:
    fontFamily: "'JetBrains Mono', ui-monospace, monospace"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.3
    fontFeature: "tnum"
  telemetry-lg:
    fontFamily: "'JetBrains Mono', ui-monospace, monospace"
    fontSize: "clamp(2.5rem, 5vw, 4rem)"
    fontWeight: 700
    lineHeight: 1
    fontFeature: "tnum"
rounded:
  sm: "2px"
  md: "4px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  panel:
    backgroundColor: "{colors.panel-surface}"
    rounded: "{rounded.md}"
    padding: "16px"
  button-preset:
    backgroundColor: "{colors.panel-surface}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
  button-preset-hover:
    backgroundColor: "{colors.panel-border}"
    textColor: "{colors.text-primary}"
  button-scan:
    backgroundColor: "{colors.safe}"
    textColor: "{colors.void-black}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px 24px"
---

# Design System: FORESIGHT

## 1. Overview

**Creative North Star: "The Flight Director"**

Every launch has one console that matters most: the Flight Director's, the one that
calls GO or NO-GO. FORESIGHT is that console for a tabletop robot — a single glanceable
surface where perception becomes a simulated future becomes a called verdict. The
aesthetic is lifted directly from rocket telemetry rooms: a near-black void, hairline
brackets around every instrument, monospace figures that tick and sweep because the
system is actually computing, and color spent on exactly one thing — the state of the
verdict. Nothing about this reads as a "dashboard app"; it reads as instrumentation
bolted onto something dangerous and real.

This system explicitly rejects the generic SaaS admin look: no soft pastel cards, no
rounded bubbly widgets, no gradient-text hero numbers, no blue/purple gradient color
story. It also rejects decoration for its own sake — no ambient sci-fi glow that isn't
tied to a real value. If a pixel is glowing, it's because a number changed.

**Key Characteristics:**
- Near-black void canvas with a faint structural grid and scanline texture, never fully flat/empty
- Corner-bracketed HUD panels, not rounded cards — precision-instrument framing
- Exactly three semantic colors (SAFE / CAUTION / BLOCK), otherwise monochrome
- All numeric telemetry in monospace with tabular figures, never proportional sans
- Motion is instrumentation, not decoration: sweeps, counts, draws — always tied to a real state change

## 2. Colors

A near-black instrument panel where color exists only to report verdict state; everything else is off-white, slate, and hairline grey.

### Primary
- **Signal Green / SAFE** (`#00e08a`): the verdict glow and gauge arc when risk is low and the action is allowed. Never used decoratively — only on verdict-linked elements (banner, gauge arc, ALLOW state, safe object highlights).

### Secondary
- **Warning Amber / CAUTION** (`#ffb020`): mid-risk verdict state — banner, gauge arc, near-edge object markers.

### Tertiary
- **Abort Red / BLOCK** (`#ff3b47`): high-risk verdict state — banner, gauge arc, danger-zone band on the table, blocked-trajectory ghost lines.

### Neutral
- **Void Black** (`#0a0e14`): the base canvas — near-black, not pure black, so panel elevation reads against it.
- **Panel Surface** (`#0d131c`): background fill for every HUD panel, one step up from void.
- **Panel Border / Hairline** (`#1c2530`, hairline `rgba(255,255,255,0.08)`): the 1px structural lines and corner brackets around every panel.
- **Grid Line** (`rgba(255,255,255,0.035)`): the background structural grid — present, but nearly subliminal.
- **Text Primary / Off-White** (`#eef2f7`): headlines, verdict text, primary numbers.
- **Text Secondary / Slate** (`#8b96a8`): labels, captions, secondary telemetry.
- **Text Tertiary** (`#5b6472`): timestamps, disabled/inactive telemetry, placeholder states.

### Named Rules
**The One Signal Rule.** SAFE / CAUTION / BLOCK are the only saturated colors anywhere in the interface, and they only ever appear attached to verdict state (the verdict banner, the risk gauge arc, the danger-zone band, per-object risk flags). If an element isn't reporting risk, it is off-white, slate, or hairline grey — no exceptions, no "just for visual interest" accent color.

## 3. Typography

**Display / UI Font:** Inter (with -apple-system, sans-serif fallback)
**Telemetry / Mono Font:** JetBrains Mono (with ui-monospace fallback)

**Character:** Inter carries every label, headline, and piece of prose with confident, slightly heavy weights — this is a console, not an editorial page, so type should feel dense and load-bearing rather than airy. JetBrains Mono is reserved entirely for anything that is a *number* — risk %, coordinates, timestamps, confidence, simulation counts — so the eye learns instantly that monospace means "live data."

### Hierarchy
- **Display** (800, `clamp(3rem, 7vw, 5.5rem)`, line-height 1): the verdict word itself (SAFE / CAUTION / BLOCK) — the single largest thing on screen.
- **Headline** (700, 1.5rem, line-height 1.15): panel titles inside HUD brackets (PERCEPTION, WORLD TWIN, DECISION).
- **Telemetry-lg** (700, `clamp(2.5rem, 5vw, 4rem)` mono, tabular figures): the risk gauge's center readout.
- **Telemetry** (500, 0.875rem mono, tabular figures): all inline numeric readouts — confidence bars, sensor noise, sim counts, coordinates, the live clock.
- **Body** (400, 0.8125rem): reasons, descriptions, object labels.
- **Label** (600, 0.6875rem, letter-spacing 0.12em, uppercase): section eyebrows and field labels *only inside instrument panels* — not used as a decorative kicker above generic content sections.

### Named Rules
**The Tabular Figures Rule.** Every number that can change at runtime (risk %, sim count, noise values, the clock) is set in JetBrains Mono with tabular figures, so digits never shift width and cause jitter as they count up.

## 4. Elevation

Flat by default, glow on state. Panels are not lifted with drop shadows or skeuomorphic depth — depth comes from a one-step-lighter surface color plus a thin border. The one exception is the verdict-linked glow: panels and the verdict banner emit a soft outer glow tinted to the current SAFE/CAUTION/BLOCK color, which intensifies as risk resolves. That glow is the only "elevation" effect in the system, and it is a live state signal, not ambient decoration.

### Shadow Vocabulary
- **panel-rest** (`border: 1px solid var(--panel-border)`, no shadow): default HUD panel state.
- **verdict-glow-safe** (`box-shadow: 0 0 24px 2px rgba(0,224,138,0.25)`): applied to the verdict banner and gauge container when verdict is SAFE.
- **verdict-glow-caution** (`box-shadow: 0 0 24px 2px rgba(255,176,32,0.25)`): CAUTION state.
- **verdict-glow-block** (`box-shadow: 0 0 28px 4px rgba(255,59,71,0.32)`): BLOCK state — slightly stronger, since a block is the highest-stakes moment.

### Named Rules
**The Earned Glow Rule.** Glow only appears in response to verdict state resolving. It never appears on hover, on idle panels, or as generic "premium" chrome — a panel that isn't reporting a verdict stays flat.

## 5. Components

### Buttons
- **Shape:** near-square corners (`rounded: 2px`) — instrument switches, not rounded app buttons.
- **Preset scenario buttons:** panel-surface background, slate label text, hairline border; on hover, border brightens to panel-border and text lifts to primary off-white. Uppercase label typography.
- **SCAN SCENE button:** filled with Signal Green at rest (`#00e08a` background, void-black text) — it is the one button allowed a saturated fill, since triggering a scan is the primary demo action and deserves the same visual weight as a verdict.
- **Free-text action input submit:** ghost/outline style matching preset buttons, not a second filled button, so SCAN SCENE stays the visually dominant action.

### Chips (confidence / object tags)
- **Style:** hairline-bordered rectangles (not pill-shaped) with a mono confidence percentage; background tints faintly toward slate.
- **State:** `near_edge: true` objects get a thin CAUTION-amber outline instead of the default hairline — the only place object-list chrome borrows verdict color, because proximity-to-edge is itself risk-relevant.

### Cards / Containers (HUD Panels)
- **Corner Style:** square (2-4px), with drawn corner-bracket accents (short L-shaped strokes at each corner, like a camera viewfinder reticle) rather than a full rounded card outline.
- **Background:** Panel Surface (`#0d131c`).
- **Shadow Strategy:** flat at rest; verdict glow only per Elevation section.
- **Border:** 1px hairline, brightened to panel-border on the panel currently "active" (e.g. DECISION panel while predicting).
- **Internal Padding:** 16px (md), 24px (lg) for the three main columns.

### Inputs / Fields
- **Style:** flat panel-surface fill, 1px hairline border, mono placeholder text in text-tertiary.
- **Focus:** border brightens to text-secondary and a faint Signal Green underline glow appears — focus is not treated as an error/caution state, so it borrows the SAFE color at low intensity.

### Navigation
- **Top bar:** single fixed row, no wrapping nav — wordmark + tagline left, live clock + connection status dot (LIVE/MOCK) + mock/live toggle right. Connection dot pulses when LIVE, holds steady when MOCK.

### Corner Bracket (Signature Component)
Every HUD panel is framed by four independent corner-bracket marks (short two-stroke L shapes, ~16px per leg, 1.5px stroke) drawn in panel-border color, brightening to the active verdict color when that panel is reporting risk-relevant state. This — not a rounded card border — is the single visual motif that makes every panel read as "instrument," and it should appear identically on all three main columns for consistency.

## 6. Do's and Don'ts

### Do:
- **Do** reserve `#00e08a` / `#ffb020` / `#ff3b47` exclusively for verdict-linked elements (banner, gauge arc, danger-zone band, near-edge flags).
- **Do** set every runtime-changing number in JetBrains Mono with tabular figures.
- **Do** frame every panel with corner brackets, not rounded card borders.
- **Do** keep the verdict word as the single largest piece of type on the screen.
- **Do** tie every glow and every animation to an actual state change in the data.

### Don't:
- **Don't** use soft pastel cards, rounded bubbly widgets, or a generic dashboard-widget grid — this must not read as a "SaaS admin template."
- **Don't** use gradient-text hero metrics or a blue/purple gradient color story.
- **Don't** add ambient glow, particle effects, or sci-fi decoration that isn't reporting a real value.
- **Don't** use a fourth accent color for anything, including charts, icons, or hover states, outside the three verdict colors.
- **Don't** use `border-left`/`border-right` colored stripes as an accent on any panel or list item.
