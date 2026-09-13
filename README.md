# FlyBrain Lab

FlyBrain Lab is a from-scratch, inspectable neural-control simulation using the
official MaleCNS v1.0 connectome. Experiment 1 contains one fly, a dynamic food
source, hunger, bilateral smell, simple vision, a compact connectome-derived
sensor-to-motor circuit, and persistent appetitive odor memory.

It is not a consciousness simulation. Neural activity shown in the terminal is
numerical model telemetry, not a claim that the simulated fly has subjective
experience.

## Requirements

- Python 3.14 virtual environment at `.venv/`
- Existing project dependencies: pandas and PyArrow
- GNU Make for the short commands below
- Official MaleCNS files in `data/raw/malecns/v1.0/`

## Run

```bash
make data-status
make run
```

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
make test         Run the complete test suite
make data-status  Verify official data, annotations, roles, and edge weights
make help         Print available commands
```

The equivalent direct command is:

```bash
.venv/bin/python -B main.py run --animate
```

## Memory

The default learned state is stored in:

```text
data/runs/experiment-001-memory.json
```

The file records versioned multipliers for official KC-to-MBON01 structural
edges. It is local runtime state and is not committed. `make run-fresh` archives
the previous file before starting with clean memory.

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
- `docs/science/learning-memory.md`: evidence, equations, IDs, and assumptions
- `docs/status.md`: current verified state and limitations
- `docs/decisions/`: architectural decision history
- `AGENTS.md`: permanent contributor and coding-agent rules

## Tests

```bash
make test
```

No neuron identifier, class, transmitter, or connection may be invented. Run
`make data-status` after changing a circuit manifest.
