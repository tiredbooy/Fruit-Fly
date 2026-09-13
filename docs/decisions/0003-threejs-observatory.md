# Decision 0003: Three.js Observatory

Date: 2026-09-13
Status: Accepted

## Context

The terminal observer exposed exact telemetry but made motion and relationships
hard to perceive. The project needed a visual interface without moving behavior
logic into a game client or weakening the world-to-brain-to-motor boundary.

## Decision

Add a framework-free TypeScript client built with Bun and Vite, render the world
with Three.js, and serve it from the Python aiohttp process. Python broadcasts a
strict versioned WebSocket schema and remains the only simulation authority.
The client may pause or resume the clock; it cannot modify fly, food, sensory,
motor, learning, memory, or neural state.

Use a responsive Persian RTL instrument interface. Show official neuron labels
and body IDs unchanged. Label the procedural neural halo as symbolic rather than
an anatomical reconstruction.

## Why

- One same-origin process gives a simple local command and avoids CORS state.
- A strict JSON boundary keeps browser concerns out of simulation packages.
- Three.js makes position, motion, food, trail, and activity visible without an
  unsupported imported biological model.
- The compact mode remains visibly useful while full mode remains available for
  topology experiments.

## Consequences

`make web` builds and serves compact mode at `http://127.0.0.1:8000`;
`make web-full` selects the complete graph. Bun is now a development requirement
for browser builds, and aiohttp is a Python runtime dependency. Three.js adds a
roughly 143 KiB gzip client bundle. WebGL failure degrades to the live data panel
instead of stopping the simulation.
