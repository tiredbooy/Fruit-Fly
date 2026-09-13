# Three.js Fly Observatory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve a responsive Three.js observatory that displays live Experiment 1 world and MaleCNS telemetry without moving behavioral authority out of Python.

**Architecture:** `main.py` composes the existing simulation and passes it to an aiohttp frontend server. The server serializes immutable `TelemetryFrame` values and streams them over one same-origin WebSocket; a framework-free TypeScript client validates snapshots, updates a Persian instrument panel, and renders the physical world plus a clearly symbolic neural halo in Three.js.

**Tech Stack:** Python 3.14, aiohttp, unittest, Bun, Vite, TypeScript, Three.js, Bun test, browser smoke testing

**Spec:** `docs/superpowers/specs/2026-09-13-threejs-observatory-design.md`

## Global Constraints

- Python remains authoritative for world, sensors, brain, learning, motor output, and body physics.
- The browser may only pause or resume the simulation clock; it cannot inject behavior.
- Browser UI text is Persian/RTL; terminal output remains English.
- Biological IDs and labels remain unchanged and come from pinned MaleCNS data.
- Neural glyph positions are symbolic, never described as anatomical coordinates.
- Compact remains the visible default; full mode is explicit and never falls back.
- Bind to `127.0.0.1` by default and reject malformed or oversized WebSocket messages.
- Cap trail/activity objects, device pixel ratio, and hidden-tab rendering work.
- Do not add React, a UI kit, external assets, remote fonts, analytics, or CDN runtime dependencies.

---

### Task 1: JSON Telemetry Boundary

**Files:**
- Create: `frontend/telemetry.py`
- Create: `tests/frontend/test_telemetry.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: `simulation.signals.TelemetryFrame`, world width/height, brain backend, dataset, FPS.
- Produces: `hello_message(...) -> dict[str, object]`, `frame_message(frame) -> dict[str, object]`, and `parse_client_command(text) -> bool` where the boolean is the requested running state.

- [ ] **Step 1: Write failing telemetry tests**

Create real signal dataclasses and assert the hello schema, optional food encoding,
sorted bounded neuron records, finite numerical values, and strict acceptance of
only `{"type":"set_running","running":bool}`. Assert malformed JSON, extra
fields, wrong types, and payloads over 1,024 bytes raise `TelemetryProtocolError`.

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -B -m unittest tests.frontend.test_telemetry -v`

Expected: import failure because `frontend.telemetry` does not exist.

- [ ] **Step 3: Implement the serializer and validator**

Use schema version `1`. Encode tuples as JSON arrays, food as `null` when absent,
and active neurons as `{body_id, label, activity}` sorted descending by activity.
Recursively reject non-finite floats before output. Parse JSON into an exact-key
dictionary and return its `running` boolean.

- [ ] **Step 4: Verify GREEN and install Python dependency**

Add `aiohttp>=3.11,<4` to `requirements.txt`, install the requirements in `.venv`,
then run the focused telemetry tests and `make test`.

- [ ] **Step 5: Commit**

```bash
git add frontend/telemetry.py tests/frontend/test_telemetry.py requirements.txt
git commit -m "feat: define browser telemetry protocol"
```

### Task 2: Same-Origin Simulation Server

**Files:**
- Create: `frontend/server.py`
- Create: `tests/frontend/test_server.py`
- Modify: `main.py`
- Modify: `experiments/experiment_001.py`
- Modify: `Makefile`

**Interfaces:**
- Consumes: an already-composed `Simulation`, `MemoryRepository`, selected backend name, dataset, world dimensions, FPS, and compiled `frontend/web/dist` path.
- Produces: `ObservatoryServer`, `create_app(...) -> aiohttp.web.Application`, and `main.py web --brain compact|full --host --port --fps --memory-file --reset-memory`.

- [ ] **Step 1: Write failing server and parser tests**

Use `aiohttp.test_utils.TestServer` with the real small Experiment 1 circuit test
composition. Assert `/health` returns schema/backend/dataset, `/ws` sends `hello`
then `frame`, pause prevents the step number advancing, resume advances it, invalid
commands return an `error` event, and missing compiled assets produce a startup
error naming `make frontend-build`. Extend parser tests for every web option.

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -B -m unittest tests.frontend.test_server tests.test_main -v`

Expected: import/parser failures for the new server and `web` command.

- [ ] **Step 3: Implement the server lifecycle**

`ObservatoryServer` owns the simulation clock and connected socket set. An aiohttp
startup task advances the simulation using monotonic deadline scheduling and
broadcasts the newest frame. WebSocket connections receive `hello` immediately.
Client commands only set the server's running flag. Cleanup cancels the tick task,
closes sockets, and delegates final memory persistence through an injected callback.

- [ ] **Step 4: Wire application composition and Make targets**

Extract only the shared compact/full network selection needed by CLI run and web.
Add `make frontend-install`, `make frontend-build`, `make web`, and `make web-full`.
`make web*` builds assets before starting the Python server. Keep existing CLI
commands backward compatible.

- [ ] **Step 5: Verify GREEN and commit**

Run focused server/parser tests and `make test`, then commit:

```bash
git add frontend/server.py tests/frontend/test_server.py main.py experiments/experiment_001.py Makefile
git commit -m "feat: stream live simulation telemetry"
```

### Task 3: Typed Browser Shell and Data Panel

**Files:**
- Create: `frontend/web/package.json`
- Create: `frontend/web/bun.lock`
- Create: `frontend/web/tsconfig.json`
- Create: `frontend/web/vite.config.ts`
- Create: `frontend/web/index.html`
- Create: `frontend/web/src/types.ts`
- Create: `frontend/web/src/snapshot.ts`
- Create: `frontend/web/src/snapshot.test.ts`
- Create: `frontend/web/src/simulation-client.ts`
- Create: `frontend/web/src/dashboard.ts`
- Create: `frontend/web/src/styles.css`

**Interfaces:**
- Consumes: schema-1 hello/frame/error WebSocket messages.
- Produces: `parseServerMessage(value): ServerMessage`, `SimulationClient`, and `Dashboard.update(frame, connection)`.

- [ ] **Step 1: Scaffold exact dependencies and write failing client tests**

Use scripts `dev`, `build`, `test`, and `typecheck`. Add runtime dependency `three`
and development dependencies `@types/three`, `typescript`, and `vite`. Tests assert
valid schema-1 messages parse, invalid/non-finite/missing fields fail, and number/
body-ID formatting remains deterministic.

- [ ] **Step 2: Install with Bun and verify RED**

Run `bun install`, then `bun test src/snapshot.test.ts`.

Expected: module/function failure before `snapshot.ts` exists.

- [ ] **Step 3: Implement typed validation and resilient socket client**

Validate untrusted JSON with explicit object ownership checks. The client exposes
connecting/open/reconnecting/incompatible states, retries with a capped backoff,
and sends only the strict pause/resume command. It stops consuming incompatible
schema frames.

- [ ] **Step 4: Implement the Persian RTL dashboard**

Use semantic HTML controls and meters. Provide compact loading, paused,
reconnecting, incompatible-schema, no-food, and WebGL-unavailable messages.
Display backend, step, hunger, bilateral senses, motor values, reward, association,
six official motor roles, and strongest-neuron rows. Preserve official labels and
IDs left-to-right inside the RTL panel.

- [ ] **Step 5: Verify and commit**

Run `bun test`, `bun run typecheck`, and `bun run build`, then commit the browser
shell and lockfile.

### Task 4: Three.js Specimen Chamber

**Files:**
- Create: `frontend/web/src/fly-scene.ts`
- Create: `frontend/web/src/main.ts`
- Modify: `frontend/web/src/styles.css`
- Modify: `frontend/web/index.html`

**Interfaces:**
- Consumes: validated `HelloMessage` and `FrameMessage` from Task 3.
- Produces: `FlyScene.resize()`, `FlyScene.update(frame)`, `FlyScene.setVisible(value)`, and a complete observatory application.

- [ ] **Step 1: Write failing pure scene-state tests**

Extract deterministic world-to-scene coordinate mapping, heading interpolation,
odor-halo scale, and neural-halo intensity into exported pure functions. Test
world corners, angle wraparound, absent food, clamping, and zero activity.

- [ ] **Step 2: Verify RED and implement scene-state functions**

Run `bun test`, observe missing exports, implement the pure functions, and rerun
until green before constructing WebGL objects.

- [ ] **Step 3: Build the reusable Three.js scene**

Create one orthographic specimen chamber with a procedural fly, translucent wings,
amber food marker, bounded odor halo, 80-point trail, and at most 64 symbolic
neural particles. Reuse geometries/materials, cap pixel ratio at 2, render through
one animation loop, disable interpolation/pulsing for reduced motion, and stop
rendering in hidden tabs.

- [ ] **Step 4: Compose client, scene, and dashboard**

`main.ts` applies each validated frame to both observers, sends pause/resume from
the single primary button, updates accessibility status, reacts to resize and
visibility events, and leaves the data panel usable if WebGL initialization fails.

- [ ] **Step 5: Verify build and commit**

Run `bun test`, `bun run typecheck`, and `bun run build`, then commit the chamber.

### Task 5: Real Browser Verification and Documentation

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/architecture.md`
- Modify: `docs/status.md`
- Create: `docs/decisions/0003-browser-observatory.md`
- Modify: `.serena/memories/frontend/core.md`
- Modify: `.serena/memories/suggested_commands.md`
- Modify: `.serena/memories/task_completion.md`
- Modify: `tests/test_project_contract.py`

**Interfaces:**
- Consumes: Tasks 1–4 and a real local browser.
- Produces: verified compact/full browser workflows and durable maintenance docs.

- [ ] **Step 1: Start compact server and inspect in a real browser**

Run `make web`, open the local URL, verify live movement and all instrument values,
pause/resume, food-absent state, narrow viewport, console errors, and keyboard focus.
Capture a screenshot for visual review and revise only concrete defects found.

- [ ] **Step 2: Verify full backend**

Run the server with `--brain full`, confirm the health/WebSocket metadata says
`full`, neural telemetry updates, and the UI does not imply that near-zero visible
movement is a transport failure.

- [ ] **Step 3: Document exact usage and ownership**

Update human and Serena docs with install/build/run commands, transport boundaries,
Persian browser versus English terminal copy, symbolic-neural-layout caveat,
security defaults, performance observations, and known full-mode calibration limit.
Add Decision 0003 for same-origin WebSocket observation around Python authority.

- [ ] **Step 4: Run complete verification**

```bash
make test
make data-status
make brain-status
make frontend-build
cd frontend/web && bun test
git diff --check
serena memories check
```

Also inspect imports to confirm `world` and `brain` remain mutually independent,
and verify no generated `dist`, `node_modules`, raw data, processed data, memory,
or secrets are staged.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md README.md Makefile frontend docs tests .serena requirements.txt main.py experiments
git commit -m "feat: add Three.js fly observatory"
```
