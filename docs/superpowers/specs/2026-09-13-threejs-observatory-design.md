# Three.js Fly Observatory Design

Date: 2026-09-13
Status: Approved

## Purpose

Add a browser frontend that makes Experiment 1 visually inspectable without
moving simulation authority into the browser. The first screen has one job:
show the fly, its changing world, and the neural signals producing movement.

This milestone visualizes the existing compact and full MaleCNS backends. It
does not add gym tasks, change neuron dynamics, calibrate full-brain motor gain,
or claim that neural telemetry represents thoughts or consciousness.

## Architecture

```text
Python simulation
  -> immutable TelemetryFrame
  -> JSON serializer
  -> same-origin WebSocket
  -> typed browser snapshot
  -> Three.js world + read-only instrument panel

Browser pause/resume command
  -> WebSocket command validation
  -> simulation clock only
```

Python remains authoritative for environment state, sensors, brain activity,
learning, motor output, and body physics. The browser never calculates behavior
and cannot inject sensory values, neuron activity, motor commands, positions,
food, hunger, or reward.

An `aiohttp` server owns one simulation session, serves the compiled frontend,
and exposes a same-origin WebSocket. The server receives a fully composed
`Simulation` from the application boundary; it does not load connectome data or
choose a neural backend. This keeps frontend infrastructure separate from the
brain and world domains.

## Commands and lifecycle

- `make web`: install/build browser assets and serve the compact backend;
- `make web-full`: install/build assets and serve the full backend;
- `make frontend-build`: type-check and compile browser assets;
- `main.py web --brain compact|full --host HOST --port PORT --fps FPS`: direct
  server entrypoint.

Compact is the default because Experiment 1 motor gain is visibly useful there.
Full mode is explicit and shows full-network activity even though current motor
output is approximately `10^-6`. It never falls back to compact.

The server runs until interrupted. It advances simulation at the configured
rate, broadcasts one latest frame per tick, persists changed memory at the
application boundary, and saves memory during orderly shutdown.

## HTTP and WebSocket contract

Endpoints:

- `GET /`: compiled application;
- `GET /assets/*`: fingerprinted Vite assets;
- `GET /health`: JSON readiness containing backend and dataset;
- `GET /ws`: live bidirectional WebSocket.

The initial WebSocket message has `type: "hello"` and includes schema version,
brain backend, dataset, frame rate, and world dimensions. Each update has
`type: "frame"` and contains only JSON-safe values from `TelemetryFrame`:

- step and elapsed time;
- body position and heading;
- optional food position/radius;
- hunger and ingestion state;
- bilateral smell and vision;
- forward and turn motor drive;
- named motor-role activity;
- bounded active-neuron records with official body ID, official label when
  available, and activity;
- trail points;
- reward and learned association strength.

The only accepted client command is
`{"type":"set_running","running":true|false}`. Unknown fields, types, oversized
messages, and malformed JSON are rejected with a short error event. Control of
the simulation clock is not control of fly behavior.

The server binds to `127.0.0.1` by default, limits WebSocket message size, and
serves no directory listing. Binding to another interface is an explicit CLI
choice.

## Browser components

The browser application uses Vite, TypeScript, and Three.js without a component
framework.

- `SimulationClient` owns WebSocket connection, schema validation, reconnect
  timing, and connection state.
- `FlyScene` owns the renderer, camera, arena, procedural fly, food, odor halo,
  trail, and symbolic neural activity field.
- `Dashboard` owns semantic DOM updates, Persian labels, pause/resume action,
  loading/error states, and accessible announcements.
- `main.ts` composes these pieces and contains no simulation rules.

The scene uses telemetry interpolation for visual smoothness only. Interpolation
does not feed values back to Python.

## Visual direction

The interface resembles a living specimen chamber rather than a generic game
dashboard.

Palette:

- chamber black `#070B0F`;
- optical slate `#14202A`;
- specimen cyan `#58D6D0`;
- food amber `#F2B84B`;
- motor magenta `#E36DA6`;
- paper white `#E8EFEF`.

Typography:

- Persian interface: system Persian-capable sans-serif stack;
- numerical instruments and body IDs: `ui-monospace` stack.

Layout:

```text
+-------------------------------------------------------------+
| connection / backend / step                    pause-resume |
+------------------------------------------+------------------+
|                                          | hunger           |
|          THREE.JS SPECIMEN CHAMBER       | smell L/R        |
|          fly + food + odor + trail       | vision L/R       |
|                                          | motor            |
|                                          | neural activity  |
+------------------------------------------+------------------+
| symbolic activity ribbon: strongest official neuron labels |
+-------------------------------------------------------------+
```

The signature element is a translucent neural halo around the fly whose pulse
comes from measured activity. Its positions are explicitly decorative and must
not be presented as anatomical coordinates. Three.js renders a procedural fly
from simple geometry so no unlicensed model asset is required.

The main action is pause/resume. Secondary camera behavior is automatic. The UI
is Persian and right-to-left, while official neuron labels and numeric IDs stay
unchanged. It supports narrow screens, keyboard focus, reduced motion, and WebGL
failure guidance.

## Loading, empty, and error behavior

- Before the socket opens: show a short Persian connecting state.
- While food is absent: keep the arena visible and show the absence as world
  state, not an error.
- While paused: retain the last frame and clearly mark the clock as paused.
- On disconnect: freeze the last valid frame, show reconnecting state, and retry
  with bounded backoff.
- On incompatible schema or invalid payload: stop applying frames and tell the
  user to rebuild/restart.
- On unavailable WebGL: keep the data panel usable and show a concise action.

## Performance

The server sends the bounded telemetry already produced by the neural backend,
not 166,606 activity values. The client reuses Three.js objects and geometries,
caps trail and activity glyph counts, limits device pixel ratio, and pauses
render work when the document is hidden. Reduced-motion mode disables ambient
pulsing and interpolation.

## Testing and acceptance

Backend tests verify exact serialization, absence of non-finite JSON, command
validation, health metadata, and WebSocket hello/frame flow. Frontend tests
verify snapshot validation and display formatting. The Vite production build
must type-check successfully.

Acceptance requires:

1. `make test` passes without changing brain/world boundaries;
2. `make frontend-build` succeeds;
3. a real browser receives live Experiment 1 telemetry;
4. the fly, dynamic food, trail, odor response, hunger, sensors, motor values,
   and bounded neuron activity visibly update;
5. pause/resume controls only the simulation clock;
6. compact and full backend launch commands both work;
7. responsive, loading, disconnected, paused, and reduced-motion states are
   verified;
8. documentation records commands, transport ownership, symbolic-layout caveat,
   and current full-mode motor limitation.

## Dependencies

Python adds `aiohttp` because the standard library does not provide a robust
same-process WebSocket and static HTTP server. Browser dependencies are
`three`, `vite`, `typescript`, and `@types/three`. No React framework, UI kit,
external model, analytics, remote font, or CDN runtime is added.
