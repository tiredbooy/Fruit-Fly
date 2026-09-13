# FlyBrain Lab

FlyBrain Lab is a from-scratch, inspectable neural-control simulation using the
official MaleCNS v1.0 connectome. Experiment 1 contains one fly, a dynamic food
source, hunger, bilateral smell, simple vision, persistent appetitive odor
memory, and selectable compact or full-connectome neural engines. Experiment 2
adds usable bench presses and dumbbell curls, 1-10 independent flies, fatigue, completed-set
rewards, separate food/gym odor memory, and a live anatomical neuron display.

It is not a consciousness simulation. Neural activity shown in the terminal is
numerical model telemetry, not a claim that the simulated fly has subjective
experience.

## Requirements

- Python 3.14 virtual environment at `.venv/`
- Python packages from `requirements.txt`: NumPy, pandas, PyArrow, SciPy, and aiohttp
- Bun 1.4 or newer for the browser build
- GNU Make for the short commands below
- Official MaleCNS files in `data/raw/malecns/v1.0/`

## Run

Run the gym with three flies:

```bash
make gym FLIES=3
```

Open <http://127.0.0.1:8000>. Enter 1-10 in the population field, apply it,
and select a fly to inspect its workout, memory, neurons, or eye camera.
Forelegs follow the moving bar/dumbbells. Three full up/down repetitions earn
a set reward. Experiment 2's explicit continuous-training apparatus keeps every
active fly at its assigned bench or curl station during a two-second recovery,
then exposes it to the next set. Repetitions still require brain-generated motor
drive and loaded joint motion. Removing a fly releases its equipment and
preserves its memory. Pause freezes physics; count changes still apply at a
clock boundary. No frontend command steers the flies.

For a finite headless gym run: `make gym-run FLIES=3`.
Gym uses the validated compact circuit, not the full brain.
See [equipment equations and measured runs](docs/science/equipment.md) for the
current model and learning-enabled/disabled comparison; the original
[resistance-lane model](docs/science/gym.md) remains documented historically.
Initial station exposure is configured, not learned. Sustained workout-seeking
has not been demonstrated; sustained attendance is externally imposed by the
experiment protocol. Reward is a model signal, not evidence
of pleasure, consciousness, or addiction. No flight physics is implemented.

After updating, stop an old server with `Ctrl+C` before running `make gym` again.
The new gym uses telemetry schema 3; the rebuilt browser also accepts the old
schema-2 gym and unchanged schema-1 Experiment 1. Memory files are unchanged.

Experiment 1 remains available unchanged:

```bash
make data-status
make run
```

Open the live Three.js observatory:

```bash
make web
```

Then visit <http://127.0.0.1:8000>. The browser shows the fly, food, odor
response, anatomical neuron activity, hunger, official descending-neuron labels,
motor output, reward, and learned association. Its only command is pause/resume;
Python remains the sole simulation authority.

The fly uses the authored, rigged visual asset you supplied in `fly-escape`.
Only appearance is reused; brain and behavior code remain independent.
Drag to orbit the 3D arena, scroll to zoom, or choose overview, fly-follow, or
fly-eye view. Eye view follows the body's heading; it is an approximate observer
camera, not a reconstruction of compound-eye vision.
The neuron panel maps actual activity onto 139,659 measured MaleCNS soma
positions. Unobserved locations differ from received zero readings; neurons
without soma positions are not assigned invented ones. Expand exact readings
for official IDs, labels, and numerical activity.
Search by ID or label to inspect a neuron; its count describes the received
subset, not all active neurons in the full brain.
The graphics label reports WebGPU when available and WebGL2 otherwise.
WebGPU rendering does not move the Python brain computation onto the GPU.
See [observatory maintenance](docs/frontend-observatory.md) for controls, source
attribution, asset rebuilding, and browser tests.

Build and run all 166,606 valid MaleCNS v1.0 neurons:

```bash
make brain-build
make brain-status
make run-full
```

The generated 198.3 MiB artifact stays under `data/processed/` and is not
committed. `make brain-build` recreates it from checksum-pinned official files.

Stop the animation with `Ctrl+C`. The terminal interface uses English text and
ASCII framing, with a fly emoji for the body. A terminal that cannot encode the
emoji automatically receives an `F` fallback.

Food starts absent, appears after a random delay, and changes position over
time. Most spawns are at least five world units from the fly; 20 percent appear
outside the accessible arena and expire later. Use a seed to replay the same
spawn sequence:

```bash
.venv/bin/python -B main.py run --animate --seed 1234
```

## Commands

```text
make run          Run Experiment 1 with persistent learned memory
make run-fresh    Archive existing memory and start with clean memory
make run-full     Run Experiment 1 with the full MaleCNS backend
make web          Build and run the Three.js observatory with compact brain
make web-full     Build and run the observatory with the full brain
make gym FLIES=3  Build and run the compact multi-fly gym
make gym-run FLIES=3  Run a finite headless gym
make gym-build    Reproduce official DM2 gym circuits
make frontend-build  Test types and build browser assets
make frontend-test   Test browser telemetry, camera fitting, and model integrity
make test         Run the complete test suite
make data-status  Verify official data, annotations, roles, and edge weights
make brain-build  Build the full memory-mapped sparse graph
make brain-status Validate the full graph and source identity
make brain-benchmark  Measure full-graph neural update speed
make help         Print available commands
```

The equivalent direct command is:

```bash
.venv/bin/python -B main.py run --animate
```

Compact remains the default. Full mode never silently falls back:

```bash
.venv/bin/python -B main.py run --animate --brain full
```

## Memory

The default learned state is stored in:

```text
data/runs/experiment-001-memory.json
```

The file records versioned multipliers for official KC-to-MBON01 structural
edges. It is local runtime state and is not committed. `make run-fresh` archives
the previous file before starting with clean memory.

Gym memories are separate: `data/runs/experiment-002/fly-N/{food,gym}-memory.json`.
Each channel is versioned and atomically saved. Corrupt/incompatible files fail
clearly. Body position, fatigue and workout totals reset on process restart;
learned memory does not. Use `--memory-dir` with separate directories for trials.

## Architecture

```text
world -> sensors -> brain adapter -> MaleCNS network -> motor -> fly body
                       ^                                  |
                       |                                  v
                learning and memory <- ingestion reward -+
```

The world exposes physics and contact only. It cannot choose walking or turning.
Hunger and learned association continuously modulate neural input instead of
triggering behavior rules.

Detailed documentation:

- `docs/architecture.md`: package boundaries and runtime sequencing
- `docs/science/equipment.md`: current bench/curl physics, assumptions and measured trials
- `docs/science/gym.md`: original resistance-lane provenance and learning model
- `docs/neural-performance-2026-09-13.md`: compact update equivalence and timing evidence
- `docs/science/learning-memory.md`: evidence, equations, IDs, and assumptions
- `docs/science/full-connectome.md`: full-graph filtering, polarity, and dynamics
- `docs/status.md`: current verified state and limitations
- `docs/decisions/`: architectural decision history
- `AGENTS.md`: permanent contributor and coding-agent rules

## Tests

```bash
make test
```

No neuron identifier, class, transmitter, or connection may be invented. Run
`make data-status` after changing a circuit manifest.
