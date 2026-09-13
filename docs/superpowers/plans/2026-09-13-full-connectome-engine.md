# Full MaleCNS Connectome Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, validate, and run a CPU sparse neural engine containing all 166,606 valid-superclass MaleCNS v1.0 neurons and 25,574,615 directed neuron-neuron edges.

**Architecture:** An offline builder filters the pinned Feather sources with the official valid-superclass rule and writes memory-mappable CSR arrays. A full-network backend implements the same neural protocol and rate equation as the existing compact backend, while CLI and Make targets select, validate, and benchmark it without changing world behavior.

**Tech Stack:** Python 3.14, NumPy, SciPy sparse, Pandas, PyArrow Feather, unittest, GNU Make

**Spec:** `docs/superpowers/specs/2026-09-13-full-connectome-engine-design.md`

## Global Constraints

- Use only checksum-pinned `male-cns:v1.0` inputs already named by the source manifest.
- Retain exactly 166,606 valid-superclass neurons, including 166,400 connected
  neurons, and 25,574,615 edges with no weight threshold.
- Preserve official body IDs and document every dynamics or polarity assumption.
- Keep `brain` and `world` mutually independent; `simulation` remains the orchestrator.
- Do not add gym, poker, Bun, or Three.js code in this milestone.
- Keep the compact backend as the default and never silently fall back from full mode.
- Generated full-graph artifacts belong under ignored `data/processed/`.

---

### Task 1: Dependency and artifact contract

**Files:**
- Create: `requirements.txt`
- Create: `brain/full_graph.py`
- Create: `tests/brain/test_full_graph.py`
- Modify: `.gitignore`
- Modify: `data/.gitignore`

**Interfaces:**
- Produces: `FullGraphMetadata`, `FullGraph`, and `FullGraphRepository.load(path: Path, source: SourceManifest) -> FullGraph`.
- Consumes: `SourceManifest` from `brain.data` and NumPy `.npy` arrays created by Task 2.

- [ ] **Step 1: Write failing repository tests**

Create fixtures containing `metadata.json`, `body_ids.npy`, `indptr.npy`,
`indices.npy`, `weights.npy`, and `signs.npy`. Assert that loading preserves
memory-mapped dtypes/shapes and rejects wrong schemas, source checksums, counts,
non-monotonic body IDs, invalid CSR boundaries, out-of-range indices, and
non-finite weights.

```python
graph = FullGraphRepository(path).load(source)
self.assertEqual((3,), graph.body_ids.shape)
self.assertEqual((4,), graph.indptr.shape)
self.assertEqual(graph.metadata.edge_count, len(graph.indices))
self.assertIsInstance(graph.weights, np.memmap)
```

- [ ] **Step 2: Run the repository tests and verify RED**

Run: `.venv/bin/python -B -m unittest tests.brain.test_full_graph -v`

Expected: import failure because `brain.full_graph` does not exist.

- [ ] **Step 3: Implement the artifact model and strict loader**

Use this public shape:

```python
@dataclass(frozen=True, slots=True)
class FullGraphMetadata:
    schema_version: int
    dataset: str
    neuron_count: int
    edge_count: int
    source_sha256: dict[str, str]
    filter_name: str
    polarity_policy: str
    dynamics: str

@dataclass(frozen=True, slots=True)
class FullGraph:
    metadata: FullGraphMetadata
    body_ids: np.ndarray
    indptr: np.ndarray
    indices: np.ndarray
    weights: np.ndarray
    signs: np.ndarray
```

Load arrays with `np.load(path, mmap_mode="r", allow_pickle=False)`. Validate
schema `1`, dataset/checksums, exact array dtypes, shapes, sorted unique body IDs,
CSR invariants, finite weights, and sign membership in `{-1, 0, 1}`.

- [ ] **Step 4: Declare existing numerical dependencies and ignores**

Create `requirements.txt` with:

```text
numpy>=2.0,<3
pandas>=2.2,<4
pyarrow>=18,<26
scipy>=1.14,<2
```

Ignore `data/processed/` at both repository and data-directory boundaries.

- [ ] **Step 5: Run tests and commit**

Run: `.venv/bin/python -B -m unittest tests.brain.test_full_graph -v`

Commit:

```bash
git add requirements.txt .gitignore data/.gitignore brain/full_graph.py tests/brain/test_full_graph.py
git commit -m "feat: define full graph artifact contract"
```

### Task 2: Official full-graph builder

**Files:**
- Create: `brain/full_graph_builder.py`
- Create: `tests/brain/test_full_graph_builder.py`
- Modify: `brain/data.py`

**Interfaces:**
- Consumes: `SourceManifest`, three pinned Feather paths, and `FullGraphMetadata`.
- Produces: `FullGraphBuilder.build(output: Path) -> FullGraphMetadata` and atomic artifact files from Task 1.

- [ ] **Step 1: Write failing filtering and normalization tests**

Build small Feather fixtures with valid, empty, and `tbc` superclasses; edges
crossing valid/invalid endpoints; and ACh/GABA/glutamate/histamine/dopamine/
missing transmitter calls. Assert that only valid-to-valid edges remain, every
valid neuron including isolated neurons is retained, IDs are sorted, and signs
are `[+1, -1, -1, -1, 0, 0]` for those calls.

For two incoming edges of weights 3 and 7, assert stored magnitudes are:

```python
denominator = np.log1p(3.0) + np.log1p(7.0)
self.assertAlmostEqual(np.log1p(3.0) / denominator, magnitude_a)
self.assertAlmostEqual(np.log1p(7.0) / denominator, magnitude_b)
```

- [ ] **Step 2: Run builder tests and verify RED**

Run: `.venv/bin/python -B -m unittest tests.brain.test_full_graph_builder -v`

Expected: import failure because `brain.full_graph_builder` does not exist.

- [ ] **Step 3: Implement batch filtering and contiguous indexing**

Define:

```python
OFFICIAL_NEURON_COUNT = 166_606
OFFICIAL_CONNECTED_NEURON_COUNT = 166_400
OFFICIAL_EDGE_COUNT = 25_574_615
FILTER_NAME = "valid-superclass-v1"
POLARITY_POLICY = "ach-positive-gaba-glu-his-negative-modulators-zero-v1"
DYNAMICS = "incoming-log1p-rate-v1"
```

Read annotations, retain truthy `superclass` values excluding strings containing
`tbc`, and filter every edge batch with both endpoints in that set. Preserve all
valid IDs, including isolated neurons. Map endpoints through `np.searchsorted`
into sorted `int64` `body_ids`. Keep edge endpoint indexes as `int32`.

- [ ] **Step 4: Implement transmitter signing and CSR generation**

Collapse consensus transmitter rows by body ID and reject conflicting non-empty
calls. Compute source-neuron signs from the documented policy. Normalize
`log1p(weight)` by total unsigned incoming magnitude per postsynaptic neuron,
multiply by the presynaptic sign, create `scipy.sparse.csr_matrix`, and save its
`indptr`, `indices`, and `data` arrays using the Task 1 filenames/dtypes.

- [ ] **Step 5: Implement real-count and atomic-publication guards**

Allow fixture tests to inject expected counts, but default to the two official
constants. Write into a temporary sibling directory, validate it with
`FullGraphRepository`, archive an existing artifact as `.bak`, and rename the
complete temporary directory into place. Restore `.bak` if publication fails.

- [ ] **Step 6: Run tests and commit**

Run:

```bash
.venv/bin/python -B -m unittest tests.brain.test_full_graph tests.brain.test_full_graph_builder -v
```

Commit:

```bash
git add brain/data.py brain/full_graph_builder.py tests/brain/test_full_graph_builder.py
git commit -m "feat: build official full MaleCNS graph"
```

### Task 3: Neural backend protocol and CSR engine

**Files:**
- Create: `brain/full_network.py`
- Create: `tests/brain/test_full_network.py`
- Modify: `brain/network.py`
- Modify: `brain/sensory.py`

**Interfaces:**
- Consumes: `FullGraph`, the compact `RuntimeCircuit` sensory/motor interface, and external `{body_id: value}` input.
- Produces: `NeuralNetwork` protocol and `FullConnectomeNetwork.step(external: dict[int, float], *, substeps: int = 5) -> NeuralSnapshot`.

- [ ] **Step 1: Write a failing compact/full parity test**

Create the same three-node graph in `RuntimeCircuit` and CSR form. Run both with
the same external input, leak, and substep count. Assert equal motor-role values
within `1e-6`, bounded activities, official body IDs in telemetry, and rejection
of interface IDs absent from the full graph.

- [ ] **Step 2: Run engine tests and verify RED**

Run: `.venv/bin/python -B -m unittest tests.brain.test_full_network -v`

Expected: import failure because `brain.full_network` does not exist.

- [ ] **Step 3: Add the backend protocol**

In `brain/network.py`, define:

```python
class NeuralNetwork(Protocol):
    circuit: RuntimeCircuit

    def step(
        self,
        external: dict[int, float],
        *,
        substeps: int = 5,
    ) -> NeuralSnapshot: ...
```

Change `BrainAdapter` to accept `NeuralNetwork`. Do not change its encoding or
learning behavior.

- [ ] **Step 4: Implement vectorized CSR dynamics**

Construct a SciPy CSR matrix without copying compatible arrays. Maintain one
`float32` activity vector and a body-ID-to-index mapping only for interface IDs.
For each substep compute sparse matrix-vector current, clamp at zero, apply
`np.tanh`, blend leak, and overwrite external indexes. Return motor roles plus
the strongest 64 nonzero neurons in `activity_by_body`; do not materialize all
166,606 entries as Python objects.

- [ ] **Step 5: Run parity and existing network tests, then commit**

Run:

```bash
.venv/bin/python -B -m unittest tests.brain.test_full_network tests.brain.test_network tests.simulation.test_loop -v
```

Commit:

```bash
git add brain/network.py brain/sensory.py brain/full_network.py tests/brain/test_full_network.py
git commit -m "feat: run sparse full-connectome dynamics"
```

### Task 4: CLI, Make targets, and benchmark

**Files:**
- Modify: `main.py`
- Modify: `Makefile`
- Modify: `tests/test_main.py`
- Create: `tests/test_full_brain_cli.py`

**Interfaces:**
- Consumes: `FullGraphBuilder`, `FullGraphRepository`, `FullConnectomeNetwork`, and the existing Experiment 1 composition.
- Produces: `brain-build`, `brain-status`, `brain-benchmark`, `run --brain`, and Make wrappers.

- [ ] **Step 1: Write failing parser and command tests**

Assert parsing and dispatch for:

```text
main.py brain-build
main.py brain-status
main.py brain-benchmark --substeps 10
main.py run --brain compact
main.py run --brain full
```

Use synthetic artifacts for command tests. Assert that missing full artifacts
return a nonzero exit with `Run 'make brain-build' first` and that full mode does
not construct `ConnectomeNetwork`.

- [ ] **Step 2: Run CLI tests and verify RED**

Run: `.venv/bin/python -B -m unittest tests.test_main tests.test_full_brain_cli -v`

Expected: parser failure for the new commands/options.

- [ ] **Step 3: Implement CLI composition**

Add constants for `data/processed/malecns/v1.0/full-graph`. `brain-build` invokes
the builder, `brain-status` invokes the repository and prints counts/policies,
and `run --brain full` injects `FullConnectomeNetwork` into `BrainAdapter` while
preserving memory persistence and the runtime circuit's sensor/motor roles.

- [ ] **Step 4: Implement benchmark output**

Load the graph, run ten warm-up substeps, then time the requested number with
`time.perf_counter`. Print graph load seconds, neuron/edge counts, milliseconds
per substep, and substeps per second. Keep output English and machine-readable
enough for documentation.

- [ ] **Step 5: Add Make targets and run tests**

Add:

```make
brain-build:
	$(PYTHON) -B main.py brain-build
brain-status:
	$(PYTHON) -B main.py brain-status
brain-benchmark:
	$(PYTHON) -B main.py brain-benchmark
run-full:
	$(PYTHON) -B main.py run --animate --brain full
```

Run: `.venv/bin/python -B -m unittest tests.test_main tests.test_full_brain_cli -v`

- [ ] **Step 6: Commit**

```bash
git add main.py Makefile tests/test_main.py tests/test_full_brain_cli.py
git commit -m "feat: expose full brain commands"
```

### Task 5: Real build, validation, and documentation

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/architecture.md`
- Modify: `docs/science/learning-memory.md`
- Modify: `docs/status.md`
- Modify: `.serena/memories/core.md`
- Modify: `.serena/memories/brain/core.md`
- Modify: `.serena/memories/suggested_commands.md`
- Modify: `.serena/memories/task_completion.md`

**Interfaces:**
- Consumes: all earlier tasks and the real pinned local MaleCNS v1.0 files.
- Produces: validated full artifact, measured benchmark, full-engine smoke evidence, and durable usage/provenance documentation.

- [ ] **Step 1: Run the real build**

Run: `make brain-build`

Expected final output:

```text
Dataset: male-cns:v1.0
Retained neurons: 166,606
Connected neurons: 166,400
Neuron edges: 25,574,615
Status: full brain artifact ready
```

- [ ] **Step 2: Validate and benchmark the artifact**

Run:

```bash
make brain-status
make brain-benchmark
```

Record actual artifact disk size, build duration, load duration, milliseconds
per substep, and substeps per second.

- [ ] **Step 3: Run the full-engine Experiment 1 smoke**

Run a finite deterministic command:

```bash
.venv/bin/python -B main.py run --brain full --steps 10 --fps 10 --seed 4 --memory-file /tmp/flybrain-full-smoke-memory.json
```

Expected: exit `0`, ten completed steps, no fallback warning, and persisted
memory compatible with Experiment 1.

- [ ] **Step 4: Update human and Serena documentation**

Document exact commands and measured results. Explain the publication's v0.9
counts versus the checksum-pinned v1.0 counts, the valid-superclass filter,
transmitter policy, full/compact selection, compact telemetry, known biological
limitations, and the fact that the next milestone is the fly gym rather than
Three.js.

- [ ] **Step 5: Run final verification**

Run:

```bash
make test
make data-status
make brain-status
git diff --check
serena memories check
```

Inspect imports to confirm no `brain` import exists under `world/` and no `world`
import exists under `brain/`.

- [ ] **Step 6: Commit implementation and measured documentation**

```bash
git add requirements.txt .gitignore AGENTS.md Makefile README.md brain docs main.py tests data/.gitignore
git commit -m "feat: integrate full MaleCNS connectome"
```
