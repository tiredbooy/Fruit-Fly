# Three.js observatory

- `main.py web` composes Experiment 1 and starts `frontend/server.py`.
- aiohttp serves `frontend/web/dist` and streams strict schema-v1 JSON on `/ws`.
- Browser commands are restricted to `{type: "set_running", running: boolean}`.
- The TypeScript client validates every server message before updating Three.js
  or the Persian RTL dashboard.
- `make web` uses compact mode; `make web-full` uses the complete MaleCNS graph.
- The current body is a user-authorized authored fly-escape rig, with independent
  skeletons, distance-sampled walking and ingestion-driven feeding. Its local
  provenance and absent public redistribution license are recorded in
  `frontend/web/src/assets/fly/walking-source.json`. The old licensed CT asset
  remains separately attributed. No reference brain/controller code is reused.
- WebGPURenderer initializes asynchronously and falls back to WebGL2. The actual
  backend is displayed; Python neural computation still runs on the CPU.
- Perspective overview/follow/eye controls affect the observer only. Eye view is
  an approximate head camera, not compound-eye biology or sensor input. The arena
  remains a 3D presentation of existing two-dimensional ground physics.
- `neuron-inspector.ts` searches all received IDs/labels and renders measured
  activity. Counts apply only to the received subset (schema maximum 128 records),
  never the entire MaleCNS brain. Zero values remain inspectable.
- Paused reconnects receive the current running state and cached frame.
- `make gym FLIES=3` starts Experiment 2 compact resistance walking and food.
  Schema 2 wraps unchanged per-fly schema-1 frames and training metrics; the
  only additional command is strict integer population setup from 1 to 10.
  Changes apply at a clock boundary even paused; selection only observes.
- The anatomical map uses 139,659 measured soma coordinates from our own pinned
  MaleCNS annotations. It colors only received matching IDs, distinguishes zero
  from unobserved, and invents no missing positions, edges or spikes.
- Gym memory is separate per fly and cue under data/runs/experiment-002/;
  removed flies are parked in-process. Full-gym/flight remain unsupported.
- `docs/frontend-observatory.md` documents asset rebuilds, browser checks, and limits.
- UI source lives in `frontend/web`; generated `dist` and `node_modules` are ignored.
- Visual tokens and layout rules are recorded in `DESIGN.md` and `.21st/design.json`.
