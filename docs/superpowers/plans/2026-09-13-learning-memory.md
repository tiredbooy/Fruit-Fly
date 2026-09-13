# Associative Learning, Persistent Memory, and Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent PAM01-gated DM1 olfactory learning, easy Makefile commands, and durable engineering/science documentation to Experiment 1.

**Architecture:** A mushroom-body component inside `brain` computes sparse Kenyon-cell activity from a deterministic official MaleCNS subgraph and applies reward-gated plasticity to official KC-to-MBON01 edges. The simulation sends ingestion reward after physics without issuing behavior commands; the brain converts learned association strength into a continuous odor-salience gain. A repository validates and atomically persists versioned synaptic multipliers.

**Tech Stack:** Python 3.14, standard-library dataclasses/JSON/pathlib, pandas and PyArrow already used by the project, unittest, GNU Make.

**Spec:** `docs/superpowers/specs/2026-09-13-learning-memory-design.md`

## Global Constraints

- All terminal output must be English ASCII.
- Only official pinned MaleCNS v1.0 body IDs, annotations, neurotransmitter calls, and edge weights may identify biological neurons or connections.
- Model assumptions must be labeled and must not be presented as measured physiology.
- `brain` and `world` may communicate only through immutable `simulation.signals` values; neither imports the other.
- Food contact may create reward but may not directly create movement or turning.
- No new Python package is required.
- Existing APIs remain backward compatible unless this plan explicitly adds optional parameters or fields with defaults.
- Tests precede implementation.
- Every material behavior, architecture, science, or command change updates its corresponding documentation.

---

### Task 1: Documentation Governance and Easy Commands

**Files:**
- Create: `AGENTS.md`
- Create: `README.md`
- Create: `Makefile`
- Test: `tests/test_project_contract.py`

**Interfaces:**
- Produces: Make targets `run`, `run-fresh`, `test`, `data-status`, and `help`.
- Produces: repository rules requiring provenance, ASCII output, dependency boundaries, TDD, status updates, science notes, and decision records.

- [ ] **Step 1: Write the failing repository-contract test**

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectContractTest(unittest.TestCase):
    def test_required_documentation_and_make_targets_exist(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("MaleCNS provenance", agents)
        self.assertIn("Documentation maintenance", agents)
        for target in ("run:", "run-fresh:", "test:", "data-status:", "help:"):
            self.assertIn(target, makefile)
```

- [ ] **Step 2: Run the test and confirm it fails because the files do not exist**

Run: `.venv/bin/python -B -m unittest tests.test_project_contract -v`

- [ ] **Step 3: Create the minimal Makefile**

```makefile
PYTHON ?= .venv/bin/python

.PHONY: run run-fresh test data-status help

run:
	$(PYTHON) -B main.py run --animate

run-fresh:
	$(PYTHON) -B main.py run --animate --reset-memory

test:
	$(PYTHON) -B -m unittest discover -s tests -t . -v

data-status:
	$(PYTHON) -B main.py data-status

help:
	@printf '%s\n' 'make run' 'make run-fresh' 'make test' 'make data-status'
```

- [ ] **Step 4: Write `AGENTS.md` and `README.md`**

`AGENTS.md` must contain these enforceable sections: project purpose, MaleCNS
provenance, no-invented-neuron policy, explicit model assumptions, dependency
boundaries, world/brain separation, English ASCII terminal output, TDD and
verification, documentation maintenance mapping, approval scope, and runtime
data policy. `README.md` must explain setup, `make` commands, current behavior,
memory location, reset behavior, and the non-consciousness limitation.

- [ ] **Step 5: Run the repository-contract test**

Run: `.venv/bin/python -B -m unittest tests.test_project_contract -v`
Expected: PASS.

---

### Task 2: Versioned Persistent Synaptic Memory

**Files:**
- Create: `brain/memory.py`
- Create: `tests/brain/test_memory.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `SynapseMemory(body_pre: int, body_post: int, baseline_weight: int, multiplier: float)`.
- Produces: `MemoryState.fresh(...)`, `MemoryState.association_strength`, and `MemoryState.with_updates(...)`.
- Produces: `MemoryRepository.load_or_create(template: MemoryState) -> MemoryState`, `save(state)`, and `reset_with_backup()`.
- Consumes: dataset and source-weights checksum strings from `SourceManifest`.

- [ ] **Step 1: Write failing memory validation and persistence tests**

Tests must prove: fresh multipliers are `1.0`; association strength is `0.0`;
a save/load round trip preserves multipliers and reward counters; a dataset,
checksum, edge-set, baseline-weight, schema-version, duplicate-edge, non-finite,
or out-of-range mismatch raises `MemoryValidationError`; save leaves no temporary
file; reset moves the old file to a `.bak` path.

```python
template = MemoryState.fresh(
    dataset="male-cns:v1.0",
    weights_sha256="abc",
    model="pam01-kc-mbon01-v1",
    plastic_edges=((101, 201, 20),),
)
repository = MemoryRepository(path)
repository.save(template.with_updates({(101, 201): 0.8}, reward=0.5))
loaded = repository.load_or_create(template)
self.assertAlmostEqual(0.8, loaded.synapses[0].multiplier)
```

- [ ] **Step 2: Run the tests and confirm import failure**

Run: `.venv/bin/python -B -m unittest tests.brain.test_memory -v`

- [ ] **Step 3: Implement immutable schema and strict validation**

Use `dataclass(frozen=True, slots=True)`. `association_strength` is
`1.0 - mean(multiplier)`, normalized by the configured range. Reject booleans as
numbers, non-finite values with `math.isfinite`, and any memory edge not exactly
matching the template.

- [ ] **Step 4: Implement atomic persistence and recoverable reset**

Create the parent directory, write sorted/indented JSON to a sibling temporary
file opened with UTF-8, flush and `os.fsync`, then `os.replace`. A reset renames
the existing file to `<name>.bak`, replacing an older backup only after the user
explicitly invoked `--reset-memory`.

- [ ] **Step 5: Add `data/runs/` to `.gitignore` and run tests**

Run: `.venv/bin/python -B -m unittest tests.brain.test_memory -v`
Expected: PASS.

---

### Task 3: Official MaleCNS Learning Circuit and Plasticity

**Files:**
- Create: `brain/learning.py`
- Create: `data/circuits/foraging-v1-learning.json`
- Create: `tests/brain/test_learning.py`
- Modify: `brain/data.py`
- Modify: `brain/circuit.py`

**Interfaces:**
- Produces: `LearningCircuit.from_json(path, annotations, transmitters, edges, expected_sha256)`.
- Produces: `LearningConfig(eligibility_decay=0.92, learning_rate=0.08, minimum_multiplier=0.35, salience_gain=1.0, active_kc_fraction=0.10)`.
- Produces: `MushroomBodyLearning.recall(smell_left, smell_right) -> RecallState`.
- Produces: `MushroomBodyLearning.reinforce(reward: float) -> LearningState`.
- Consumes: `MemoryState` and returns a changed `MemoryState` without file I/O.

- [ ] **Step 1: Materialize a deterministic official learning artifact**

Select official `DM1_lPN` bodies `10176` and `10208`, official `MBON01` bodies
`10013` and `520151`, and official dopamine-called `PAM01` bodies. For each
hemisphere, retain official DM1_lPN-to-KC-to-MBON01 paths where both structural
weights are at least 10. Rank by descending `min(PN->KC, KC->MBON)`, then
descending product, then ascending KC body ID, retaining 24 KCs per hemisphere.
Store every selected body ID and exact weight plus the source-weights checksum.

- [ ] **Step 2: Write failing provenance and learning tests**

Tests must prove that every ID/type/class/transmitter and every edge matches the
pinned local MaleCNS files; `PAM01` is accepted only as dopamine modulation and
never as signed fast current; sparse recall activates only the configured top
fraction; eligibility decays without odor; zero reward changes no multiplier;
reward changes only eligible KC-to-MBON edges; multipliers never cross `0.35`;
and association strength increases continuously after learning.

```python
learner.recall(smell_left=0.8, smell_right=0.1)
before = learner.memory
event = learner.reinforce(1.0)
self.assertTrue(event.changed)
self.assertGreater(event.memory.association_strength, before.association_strength)
```

- [ ] **Step 3: Add a transmitter-call API that distinguishes modulation**

Keep `NeuronTransmitters.require_known` for fast ACh/GABA polarity. Add
`require_call(body_id, expected)` for exact official calls such as dopamine and
glutamate without assigning them an invented fast-current sign.

- [ ] **Step 4: Implement circuit loading and validation**

Validate dataset checksum, unique IDs, official types/classes, hemispheric
pairing, all edge triples, minimum weight, and exact plastic-edge declarations.
Reject a dopamine body appearing as the presynaptic source of a fast edge.

- [ ] **Step 5: Implement recall, eligibility, and plasticity as pure state transitions**

PN and KC activations use normalized `log1p(weight)` structural weights. Sparse
coding retains the configured top fraction per side. Eligibility is
`decay * previous + (1 - decay) * KC activity`. Reward update is
`new_multiplier = max(minimum, old - learning_rate * reward * eligibility * (old - minimum))`.
Learned salience is `1 + salience_gain * association_strength`.

- [ ] **Step 6: Run brain tests**

Run: `.venv/bin/python -B -m unittest tests.brain.test_learning tests.brain.test_memory tests.brain.test_data tests.brain.test_circuit -v`
Expected: PASS.

---

### Task 4: Simulation, Telemetry, CLI, and ASCII Visualization

**Files:**
- Modify: `brain/sensory.py`
- Modify: `simulation/signals.py`
- Modify: `simulation/loop.py`
- Modify: `experiments/experiment_001.py`
- Modify: `frontend/console.py`
- Modify: `main.py`
- Modify: `tests/brain/test_network.py`
- Modify: `tests/simulation/test_loop.py`
- Modify: `tests/frontend/test_console.py`
- Modify: `tests/test_main.py`

**Interfaces:**
- Adds: `RewardSignal(amount: float)` and `LearningSnapshot(reward, association_strength, eligibility, active_kcs, changed)`.
- Adds optional `learning` field to `TelemetryFrame`.
- Adds `BrainAdapter.learn(reward: RewardSignal) -> LearningSnapshot`.
- Adds CLI options `--memory-file PATH` and `--reset-memory`.

- [ ] **Step 1: Write failing integration and CLI tests**

Tests must prove that sensory processing precedes movement, ingestion precedes
reward, reward changes memory only after an eligible odor observation, learned
salience increases encoded ORN input continuously, telemetry reports the event,
renderer output is ASCII, CLI defaults to the documented memory path, and reset
is parsed.

- [ ] **Step 2: Extend immutable boundary signals**

Keep defaults so existing test fixtures remain valid. Reward is clamped to
`0.0..1.0`. Learning telemetry contains numbers and counts only; it does not
expose mutable memory objects across boundaries.

- [ ] **Step 3: Integrate learning without crossing architecture boundaries**

`BrainAdapter.step` calls mushroom-body recall before encoding sensory input.
The salience multiplier is applied to bilateral odor channels alongside hunger.
`Simulation.step` computes ingestion after movement, constructs `RewardSignal`,
and calls `BrainAdapter.learn`. No method in `world` imports or calls learning.

- [ ] **Step 4: Integrate persistence lifecycle in `main.py`**

Load or create memory before composition. If `--reset-memory` is supplied,
archive it first. Save whenever a telemetry frame reports a changed memory and
again in `finally` before restoring the terminal. Convert all failures to short
English ASCII messages with a non-zero exit code.

- [ ] **Step 5: Add visible learning telemetry**

Render `Reward`, `Association`, `Eligible KCs`, and `MEMORY UPDATED` using only
ASCII characters. Keep arena dimensions responsive and preserve cursor cleanup.

- [ ] **Step 6: Run integration tests and a two-session smoke check**

Run the full test suite, then run two finite CLI sessions against a temporary
memory path. Confirm the second file has a larger association strength and that
all terminal bytes are ASCII.

---

### Task 5: Architecture, Science, Status, and Decision Documentation

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/science/learning-memory.md`
- Create: `docs/status.md`
- Create: `docs/decisions/0001-learning-memory.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Test: `tests/test_project_contract.py`

**Interfaces:**
- Produces: one discoverable source for current status, one stable architecture
  description, one scientific evidence/assumption ledger, and one decision
  history.

- [ ] **Step 1: Extend documentation-contract tests**

Require every document, current commands, the memory schema version, selected
official neuron classes, equations, dependency rule, limitations, test command,
and source links. Assert all user-facing command examples match parser options.

- [ ] **Step 2: Write architecture documentation**

Document package responsibilities, allowed imports, immutable boundary signals,
tick order, persistence ownership, failure behavior, and an ASCII data-flow
diagram. Explain why learning remains inside `brain` and persistence remains at
the application boundary.

- [ ] **Step 3: Write the science and assumption ledger**

List exact selected body IDs, types, sides, neurotransmitter calls, official
edge weights, dataset/checksum provenance, selection algorithm, plasticity
equation, parameters, supporting primary sources, and every non-data-derived
assumption. State explicitly what is not modeled.

- [ ] **Step 4: Write status and decision documents**

`docs/status.md` records the date, implemented behavior, verified commands and
results, known limitations, and next milestone. The ADR records context, chosen
mushroom-body approach, consequences, and why direct ORN-motor plasticity and
episodic coordinate memory were rejected.

- [ ] **Step 5: Run final verification**

Run:

```bash
make test
make data-status
make help
.venv/bin/python -B main.py run --steps 600 --fps 30 --memory-file /tmp/flybrain-memory.json
git diff --check
```

Confirm: every test passes; all official runtime and learning edges validate;
the finite run records at least one reward event; the memory JSON reloads; the
second identical run starts with the saved association; CLI output is ASCII;
and no `brain`/`world` cross-import exists.
