# Experiment 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run one deterministic MaleCNS-backed fly with one food source, hunger-modulated smell, simple vision, neural motor output, and observable Persian telemetry.

**Architecture:** A modular monolith keeps `brain` and `world` independent. `SimulationLoop` transports immutable numeric signals between them, while a read-only console observer displays and records activity. Official MaleCNS data and explicit model assumptions are validated separately.

**Tech Stack:** Python 3.14 standard library, NumPy, SciPy, pandas, PyArrow, `unittest`

**Spec:** `docs/superpowers/specs/2026-09-12-experiment-1-architecture-design.md`

## Global Constraints

- Use official MaleCNS `v1.0` IDs, types, annotations, and connectivity only.
- Do not copy another fly-brain project or add a neural-simulator framework.
- Do not translate world facts directly into behavior.
- Record every non-connectomic dynamical choice as a model assumption.
- Keep all visible terminal text in Persian.

---

### Task 1: Official data and provenance boundary

**Files:**
- Modify: `brain/data.py`
- Create: `brain/circuit.py`
- Create: `data/malecns/v1.0/source-manifest.json`
- Create: `data/circuits/foraging-v1.json`
- Create: `tests/brain/test_data.py`
- Create: `tests/brain/test_circuit.py`

**Interfaces:**
- Produces: `MaleCNSAnnotations`, `ConnectomeEdges`, `CircuitManifest`, and validation errors.
- Consumes: official Feather files and JSON manifests.

- [ ] Write tests proving annotation rows retain `bodyId`, type, instance, side, status, retinal coordinates, and source provenance.
- [ ] Run `python -m unittest tests.brain.test_data tests.brain.test_circuit -v` and confirm failure because the data boundary does not exist.
- [ ] Implement immutable data records, Feather readers, SHA-256 validation, manifest loading, selector resolution, and bilateral/type checks.
- [ ] Add the pinned official `v1.0` source URLs and verified DNp09/DNa01/DNa02 annotations to the manifests.
- [ ] Re-run the tests and confirm they pass.

### Task 2: World, physiology, and physical sensors

**Files:**
- Modify: `world/environment.py`
- Modify: `world/fly.py`
- Modify: `world/motor.py`
- Create: `world/food.py`
- Create: `world/sensors.py`
- Create: `simulation/signals.py`
- Create: `tests/world/test_environment.py`
- Create: `tests/world/test_fly.py`
- Create: `tests/world/test_sensors.py`

**Interfaces:**
- Produces: `SensoryFrame(smell_left, smell_right, vision_left, vision_right)`, `FlyState`, and physical contact events.
- Consumes: `MotorDrive(forward, turn)`, fixed timestep, and immutable environment state.

- [ ] Write tests for odor falloff, mirrored bilateral samples, bounded hunger, metabolic increase, food consumption, and body integration.
- [ ] Run the world tests and confirm failure because the domain objects do not exist.
- [ ] Implement immutable value objects and deterministic physical systems without importing `brain`.
- [ ] Model vision as grayscale angular contrast and ingestion as an explicitly documented contact simplification.
- [ ] Re-run the world tests and confirm they pass.

### Task 3: Neural dynamics, sensory modulation, and motor readout

**Files:**
- Modify: `brain/neuron.py`
- Modify: `brain/network.py`
- Modify: `brain/sensory.py`
- Create: `brain/modulation.py`
- Create: `brain/readout.py`
- Create: `tests/brain/test_network.py`
- Create: `tests/brain/test_sensory.py`
- Create: `tests/brain/test_modulation.py`
- Create: `tests/brain/test_readout.py`

**Interfaces:**
- `RateNetwork.step(external_input: ndarray) -> ndarray`
- `SensoryEncoder.encode(frame: SensoryFrame, hunger: float) -> ndarray`
- `MotorReadout.decode(activity: ndarray) -> MotorDrive`

- [ ] Write tests for deterministic sparse propagation, continuous ORN hunger gain, bilateral sensory mapping, DNp09 forward output, and DNa01/DNa02 steering output.
- [ ] Run the brain tests and confirm failure because the neural components do not exist.
- [ ] Implement a bounded leaky rate model using SciPy sparse matrices and explicit configuration for every model assumption.
- [ ] Keep unknown transmitter polarity explicit and reject it unless the circuit manifest contains an approved assumption.
- [ ] Re-run the brain tests and confirm they pass.

### Task 4: Simulation loop and observable neural trace

**Files:**
- Create: `simulation/telemetry.py`
- Create: `simulation/loop.py`
- Create: `frontend/__init__.py`
- Create: `frontend/console.py`
- Create: `tests/simulation/test_loop.py`
- Create: `tests/frontend/test_console.py`

**Interfaces:**
- `SimulationLoop.step() -> TelemetryFrame`
- `ConsoleRenderer.render(frame: TelemetryFrame) -> str`
- `JsonlRecorder.record(frame: TelemetryFrame) -> None`

- [ ] Write tests proving the loop order, immutable telemetry, causal activity fields, Persian labels, deterministic replay, and observer isolation.
- [ ] Run the simulation/frontend tests and confirm failure because the loop and observers do not exist.
- [ ] Implement the fixed-step coordinator, rate-limited console renderer, and JSONL recorder.
- [ ] Ensure console and recorder can observe but cannot mutate simulation state.
- [ ] Re-run the simulation/frontend tests and confirm they pass.

### Task 5: Experiment 1 walking skeleton

**Files:**
- Create: `experiments/experiment_001.toml`
- Create: `experiments/__init__.py`
- Create: `experiments/experiment_001.py`
- Modify: `main.py`
- Create: `tests/test_architecture.py`
- Create: `tests/test_experiment_001.py`
- Create: `pyproject.toml`

**Interfaces:**
- `build_experiment(config_path: Path) -> SimulationLoop`
- CLI: `python main.py --steps N --no-ansi --record PATH`

- [ ] Write tests preventing `brain`/`world` cross-imports and exercising a deterministic end-to-end run with one fly and one food source.
- [ ] Run the complete suite and confirm the new acceptance tests fail for missing composition.
- [ ] Implement TOML configuration, dependency composition, CLI arguments, and graceful validation errors in Persian.
- [ ] Run `python -m unittest discover -s tests -t . -v` and verify zero failures.
- [ ] Run a short real-data Experiment 1 smoke test and verify telemetry contains official IDs, sensor activity, neural activity, and motor output.
