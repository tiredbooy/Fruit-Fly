# Architecture

## Purpose

FlyBrain Lab is a modular, inspectable neural-control simulation. Experiment 1
uses one fly, one dynamic food source, hunger, smell, simple vision, persistent
appetitive odor learning, and either a compact or full MaleCNS neural backend.

The architecture prevents environment code from deciding behavior. Every turn
and forward movement must pass through sensors, neural computation, and motor
readout.

## Package responsibilities

| Package | Responsibility | May depend on |
| --- | --- | --- |
| `world` | Geometry, odor physics, randomized food lifecycle, food contact, body movement, physiology | `simulation.signals` |
| `brain` | MaleCNS data, graph building, compact/full neural dynamics, modulation, learning, memory state | `simulation.signals` |
| `simulation` | Immutable boundary signals and tick orchestration | `brain`, `world` |
| `experiments` | Concrete Experiment 1 composition and parameters | `brain`, `simulation`, `world` |
| `frontend` | Terminal rendering, versioned browser telemetry, aiohttp host | `simulation.signals` |
| `frontend/web` | Persian RTL Three.js observer and instruments | JSON telemetry only |
| `main.py` | CLI, official asset loading, memory persistence lifecycle | all composition adapters |

The dependency rule is explicit: **world must not import brain**, and brain must
not import world. Data crosses those boundaries through immutable dataclasses in
`simulation/signals.py`.

## Continuous control loop

```text
+---------+     +---------+     +-------------+     +----------+
|  WORLD  | --> | SENSORS | --> | BRAIN       | --> | MOTOR    |
| food    |     | smell L |     | hunger gain |     | forward  |
| fly     |     | smell R |     | memory gain |     | turn     |
| fields  |     | vision  |     | MaleCNS net |     +----+-----+
+----+----+     +---------+     +-------------+          |
     ^                                                     |
     +-------------------- FLY BODY <----------------------+
```

No component can shortcut this loop with rules such as `food left -> turn left`
or `hunger high -> seek food`.

## Learning loop

```text
DM1 odor -> DM1_lPN -> sparse Kenyon cells -> MBON01 response
                              |
                              +-> eligibility trace
                                        |
food contact -> ingestion -> PAM01 reward
                                        |
                                        v
                              KC-to-MBON01 plasticity
                                        |
                                        v
                           learned odor-salience gain
```

Food contact creates a normalized reward signal after body physics. It never
creates a motor command. `BrainAdapter` applies the learned salience gain to the
next odor encoding, and the existing MaleCNS-derived network still produces the
motor output.

## Tick ordering

`Simulation.step(dt)` performs these operations in order:

1. `Environment` advances the random food lifecycle and may expose no food.
2. `SensorRig` samples physical smell and vision.
3. `BrainAdapter` recalls the odor representation and updates KC eligibility.
4. Hunger and learned salience continuously scale bilateral odor input.
5. The selected `NeuralNetwork` backend advances five neural substeps.
6. `MotorReadout` converts named descending-neuron activity to forward/turn
   drive.
7. `FlyBody` moves and `Environment` constrains its position.
8. Physical food contact changes hunger, creates one reward, and removes the food.
9. The brain applies PAM-gated plasticity and returns immutable telemetry.
10. The application boundary atomically persists changed memory.

The food lifecycle is physical world state. It uses a local random generator,
waits between spawns, expires uneaten food, usually places food far inside the
arena, and sometimes places it outside the fly's accessible bounds. Missing food
produces zero smell and vision rather than a behavioral instruction.

This order ensures that reward modifies the odor representation that preceded
the rewarded contact.

## Browser observation boundary

```text
Python simulation -> immutable frame -> JSON schema v1 -> WebSocket -> Three.js
       ^                                                        |
       +---------------- pause/resume clock only <---------------+
```

`main.py web` composes the same Experiment 1 simulation used by the terminal.
`ObservatoryServer` serves built Vite assets and broadcasts finite, bounded JSON
frames. It rejects cross-origin WebSockets, oversized messages, unknown fields,
and every command except `set_running` with a Boolean value. The browser parses
the schema again before rendering, so incompatible telemetry stops visibly.

The browser never imports Python domain objects and cannot send motor, sensor,
food, hunger, reward, memory, or neural values. Three.js renders an authored
skeletal fly, world position, food, odor strength, and a trail.
The Persian instrument panel remains usable if graphics or model loading
fails. Connecting observers receive the current running state and latest frame,
including when the simulation is paused.

`main.ts` opens telemetry before lazily loading `fly-scene.ts`. The scene awaits
`WebGPURenderer.init()`, loads the local GLB, and compiles materials; the latest
hello/frame/running values are replayed after initialization. Three.js falls back
to WebGL2 when a WebGPU adapter cannot initialize, and the UI names the actual
backend. Browser rendering never moves neural computation onto the GPU.

Broadcast handles connection-reset/broken-pipe errors per observer, removes
only the disconnected socket and continues the shared clock. A socket can close
between the readiness check and the asynchronous send. Cancellation and
serialization/programming errors are not swallowed as network disconnects.

`scene-camera.ts` owns perspective orbit, zoom, overview, fly follow, and the
head-height eye camera. Eye pose is derived only from rendered body position and
heading, with orbit disabled until the observer exits eye mode. The selected
body mesh is hidden in eye mode to avoid occlusion. This is
not photoreceptor rendering and is not fed back to the Python vision sensors.
`world-scene.ts` supplies arena solids and lighting. The X/Z ground plane maps
the existing Python x/y coordinates; this is a 3D view of ground-walking physics,
not flight or a new collision model. Camera actions cannot become motor input.

`neuron-inspector.ts` renders the received `neural.active` records; the existing
schema caps this collection at 128. `neuron-readings.ts` provides pure filtering
and ordering without changing the frame. Labels and IDs come from telemetry;
bar length is bounded while numeric readings retain small nonzero values. The
positive-activity count is explicitly scoped to received records. No new neuron
selection, invented connection, or whole-brain activity claim is introduced.

The anatomical viewer joins received IDs to 139,659 measured soma locations
exported from our pinned annotations, out of 166,606 eligible bodies. Missing
positions are counted, never synthesized. A separate renderer shows unobserved,
received-zero and received-positive points; no fabricated edges or spikes.
The exact numeric list remains behind a disclosure. Both renderers can fail
independently without stopping telemetry.

The current authored rig is reused with the user's authorization from their
fly-escape project. Only appearance and skeletal animation are reused; no brain,
controller or anatomy dataset is copied. Its manifest records the source commit,
checksum and absence of a supplied public redistribution license. Each fly has
an independent skeleton/mixer, with shared geometry/materials. Actual cumulative
displacement samples the walking clip; ingestion samples feeding. Neither can
move the Python-owned body root. There is no flight state.

The previous visual asset pipeline remains available separately:
`scripts/build_fly_asset.py` verifies the licensed Zenodo archive and reduces
four external CT surfaces into a locally served GLB. Its provenance manifest,
attribution, and checksums are tracked beside the asset. The female surface is
appearance only, not the male connectome specimen. See
[observatory maintenance](frontend-observatory.md) and
[decision 0004](decisions/0004-webgpu-ct-fly.md).

## Experiment 2 gym boundary

`experiments/experiment_002.py` composes `GymSimulation`, `Environment`, an
`EquipmentFloor`, and one
`GymBrainAdapter` per fly. The compact runtime adds validated DM2 cue paths to
the preserved food/vision circuit. Food and synthetic gym odor have separate
eligibility and KC-to-MBON memory. Mapping DM2 to the apparatus odor, resistance,
fatigue, fitness and reward scale are explicit model assumptions, documented in
[equipment science](science/equipment.md), with the original learning/lane model
in [gym science](science/gym.md). No world code selects destinations or steers flies.

Each neural interval (at most 0.1 seconds) advances the shared food schedule,
samples each fly's real sensors, advances independent brains, and applies
descending motor output. Contact with unoccupied equipment enables the model
foreleg actuator; supported body pose and a loaded scalar joint are world state.
Joint physics uses steps at most 0.01 seconds. Positive vertical displacement
earns work; three full up/down strokes earn one set and a bounded reward. Partial
strokes never earn sets. Default Experiment 2 enables a continuous-training
apparatus: after a set, the occupied station racks its weight, retains the grip
and support pose for two seconds, then permits another neurally driven set. The
apparatus prevents locomotion while attached but never supplies lifting work.
Physiology follows actual work, and reward modifies the eligibility preceding
the physical outcome. Ground food cannot be ingested while a body is supported
in an elevated equipment pose.

`gym_cli.py` owns construction and storage. Each stable `fly-N` has separate
food/gym memory under `data/runs/experiment-002/`; Experiment 1's file is untouched.
All ten slots are validated at startup. Reducing count parks bodies and memory
in a bounded bank; increasing restores them. Physiology/work counters restart
with the process. Memory writes are atomic per file, not one cross-file transaction.

`GymObservatoryServer` uses explicit schema 3 for articulated equipment without
changing Experiment 1's schema 1. Its hello supplies station kinds, positions,
headings, loads, travel, contact radius and population. A `gym_frame` wraps an
unchanged schema-1 frame, training metrics and immutable `ExerciseSnapshot` for
each active fly. The browser retains a schema-2 parser for older lane servers.
The only new
command is strict integer `set_population` (1-10), applied at the next clock
boundary, even when paused. Applying, stepping and caching occur before any
await; a request arriving during broadcast waits for the next boundary and its
own acknowledgement. New clients receive current population and cached state.

The browser count changes experiment setup, not behavior. Selecting a fly
changes only the camera, anatomy and instruments. Station geometry comes from
Python; there are no browser-only positions. The default physical grid exposes
flies to ten alternating bench/curl stations initially, explicitly not evidence
of learned gym seeking. Continuous station attendance is also imposed experiment
setup, not a world-selected behavior. Reducing population releases an occupied
station without reward and retains inactive body, neural, memory and recovery state.
Gym full-connectome mode is rejected until separately calibrated and measured.

`EquipmentScene` uses one authoritative stroke to position weights and derive
grips. `ForelegPose` solves the authored two-segment forelegs to those grips;
each fly has an independent skeleton. `AnimatedFly` applies received support
posture without moving the physical root. Eye observation uses the rendered head
and support orientation while attached. This observer remains distinct from
the Python simple-vision input. Static apparatus meshes are merged by material.

The compact network caches immutable normalized edge weights and labels but
preserves original update order and returns independent snapshot dictionaries.
The live inspector caches received-ID DOM rows and updates their exact values,
reordering existing elements only when the activity order changes. Neither
optimization drops neurons or changes rates; see [measured equivalence and
timings](neural-performance-2026-09-13.md).

## Runtime circuits

`data/circuits/foraging-v1-runtime.json` contains the compact sensor-to-motor
subgraph. `data/circuits/foraging-v1-learning.json` contains the mushroom-body
learning subgraph. Both declare the SHA-256 of the official weights asset.

`make data-status` validates:

- dataset and asset checksums;
- role IDs, types, classes, sides, and transmitter calls;
- every compact edge triple against the 151,856,684-row official weights file;
- supported fast-current polarity and dopamine-only modulation.

## Full-connectome backend

`make brain-build` converts the pinned v1.0 Feather assets into a SciPy CSR
matrix at `data/processed/malecns/v1.0/full-graph/`. The builder keeps all
166,606 annotations passing the official valid-superclass filter, including 206
isolated bodies, and keeps 25,574,615 edges whose endpoints both pass it.

The artifact stores sorted `body_ids`, CSR `indptr` and `indices`, normalized
signed `weights`, transmitter `signs`, and provenance metadata as NumPy files.
The repository opens arrays with memory mapping and rejects incompatible schema,
dataset, source checksums, dtypes, shapes, IDs, indices, nonfinite values, or
counts.

Both `ConnectomeNetwork` and `FullConnectomeNetwork` implement the same
`NeuralNetwork` boundary consumed by `BrainAdapter`. The experiment and world do
not know which backend is active. `main.py run --brain full` selects the full
backend explicitly; missing or stale artifacts stop with an instruction to run
`make brain-build` rather than falling back to compact.

Full-network telemetry retains every configured interface body and fills the
remaining 128-record budget with at most 64 strongest positive non-interface
bodies. Equal rates use ascending body ID. The current 70-body interface leaves
58 extra slots; configurations exceeding 128 interface bodies fail explicitly.
This corrects an intermittent overflow in the earlier union-of-interface-and-top64
selection without changing neural updates. It keeps the terminal and
Python object allocation bounded while all 166,606 activities continue updating
inside NumPy/SciPy arrays.

## Memory ownership

`MushroomBodyLearning` owns in-process eligibility and immutable `MemoryState`.
It performs no file I/O. `MemoryRepository` is a JSON gateway used by `main.py`.
The default file is `data/runs/experiment-001-memory.json`.

The persisted schema binds memory to:

- schema version `1`;
- dataset `male-cns:v1.0`;
- official weights checksum;
- model `pam01-kc-mbon01-v1`;
- exact KC-to-MBON01 edge IDs and baseline weights.

Writes use a temporary sibling file, `fsync`, and atomic replacement. A reset
moves existing state to `.bak` before starting clean.

## Failure behavior

- Missing or corrupt official assets stop before simulation.
- Missing, stale, or malformed full-graph artifacts stop full mode before simulation.
- An invented or mismatched learning role or edge stops validation.
- An incompatible memory schema, dataset, model, checksum, or edge set is
  rejected instead of silently reset.
- A failed save exits with an English ASCII error.
- `Ctrl+C` restores the terminal and saves the current memory.
- An incompatible browser telemetry schema stops rendering and reports the
  mismatch instead of guessing field meanings.

## Extension points

Future experiments can add other odor channels, aversive PPL1 reinforcement,
visual associations, extinction, and memory consolidation by adding explicit
circuit manifests and learning models. They must not add environment-to-action
shortcuts or reuse DM1 association values as a universal memory system.
