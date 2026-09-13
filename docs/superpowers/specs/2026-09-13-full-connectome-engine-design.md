# Full MaleCNS Connectome Engine Design

Date: 2026-09-13
Status: approved for implementation

## Goal

Add a runnable full-connectome backend for MaleCNS v1.0 while preserving the
existing Experiment 1 world, sensory adapters, motor adapter, learning memory,
and compact backend. The full backend advances all 166,606 MaleCNS v1.0 neurons
with a valid official superclass, including 166,400 connected neurons and 206
isolated neurons, plus all 25,574,615 directed edges between valid neurons.

This milestone does not implement the gym, poker, or Three.js. Those remain
later milestones built on the full engine and its telemetry boundary.

## Scientific source of truth

The builder consumes the three checksum-pinned local assets already named in
`data/malecns/v1.0/source-manifest.json`:

- body annotations;
- segment-to-segment connection weights;
- consensus neurotransmitter predictions.

The neuron filter follows the MaleCNS publication's counting notebook: a neuron
must have a non-empty `superclass` that does not contain `tbc`, and both endpoints
of every retained edge must pass that filter. No connection-weight threshold is
applied. The build must fail unless the result is exactly 166,606 retained
neurons, 166,400 connected neurons, and 25,574,615 edges for `male-cns:v1.0`.

The publication and its counting notebook describe the earlier v0.9 graph as
166,691 proofread neurons and 166,391 connected neurons. Janelia documents minor
proofreading and annotation refinements in v1.0. The checksum-pinned local v1.0
tables are authoritative for this engine and produce the counts above.

Body IDs, superclass/type/class annotations, transmitter calls, and structural
weights remain data-derived. Rate dynamics, polarity interpretation, leak,
normalization, and temporal scale remain explicit simulator assumptions.

## Architecture

```text
OFFLINE BUILD
official Feather files
        |
        v
valid-superclass filter
        |
        v
body-ID indexing + polarity policy + CSR conversion
        |
        v
data/processed/malecns/v1.0/full-graph/

RUNTIME
world sensors -> BrainAdapter -> NeuralNetwork protocol
                                      |
                         +------------+------------+
                         |                         |
                  compact backend          full CSR backend
                         |                         |
                         +------------+------------+
                                      |
                               MotorReadout
```

`brain` remains independent of `world`. `simulation` continues to orchestrate
the loop. The frontend consumes only `TelemetryFrame` and does not know which
neural backend produced it.

## Processed artifact

The generated directory contains independently memory-mappable arrays:

- `body_ids.npy`: sorted official body IDs (`int64`);
- `indptr.npy`: CSR row boundaries (`int64`);
- `indices.npy`: presynaptic contiguous indexes (`int32`);
- `weights.npy`: normalized signed edge values (`float32`);
- `signs.npy`: per-neuron fast-transmission sign (`float32`);
- `metadata.json`: schema, dataset, source checksums, counts, filter, polarity
  policy, and dynamics identifier.

Generated artifacts live under `data/processed/` and are ignored by Git. They
are reproducible from pinned official inputs. Writes use a temporary sibling
directory and atomic rename so an interrupted build cannot appear valid.

## Transmitter policy

The full graph needs an explicit fast-current interpretation:

- acetylcholine: `+1`;
- GABA, glutamate, and histamine: `-1`;
- dopamine, serotonin, octopamine, other modulators, unclear, and missing: `0`.

This policy is a documented model assumption. Monoamines are not silently
treated as excitatory currents. The builder records counts for every consensus
transmitter and every resulting sign.

## Dynamics

The CSR matrix is stored with postsynaptic neurons as rows and presynaptic
neurons as columns. For structural weight `w` and presynaptic sign `s`, each
stored value is:

```text
A[post, pre] = s(pre) * log(1 + w) / sum_incoming(log(1 + w))
```

Each neural substep uses the existing Experiment 1 rate model:

```text
current = A @ activity
driven = tanh(max(0, current))
activity = leak * activity + (1 - leak) * driven
```

External sensory values overwrite their officially selected input neuron states
after every substep, exactly as in the compact backend. Existing descending
neuron body IDs provide motor activity.

## Runtime interface

A small `NeuralNetwork` protocol exposes `step(external, substeps)` and returns
`NeuralSnapshot`. Both compact and full engines implement it. `BrainAdapter`
depends on this protocol rather than the compact concrete class.

The full engine never converts all 166,391 activities into a Python dictionary
per frame. `NeuralSnapshot.activity_by_body` contains motor-role neurons,
externally stimulated neurons, and a bounded top-activity sample for inspection.
The complete state remains a contiguous NumPy array inside the engine.

## CLI and Make targets

Commands:

- `make brain-build`: construct or replace the processed full graph;
- `make brain-status`: validate artifact metadata, shapes, and source checksums;
- `make run-full`: run Experiment 1 with the full backend;
- `main.py run --brain compact|full`: select the backend explicitly.

`compact` remains the default so existing commands and tests remain fast. A
missing or incompatible full artifact produces an actionable error pointing to
`make brain-build`; it never silently falls back to compact mode.

## Performance strategy

The target machine has 61 GiB RAM, a 16-thread Ryzen 7 7700X, NumPy 2.5.3,
SciPy 1.18.1, and no available NVIDIA runtime. The first implementation targets
CPU SciPy sparse matrix-vector multiplication.

The build processes source weights in Arrow batches and avoids Python objects
per edge. Runtime arrays are `float32`/`int32` where safe. A benchmark command
reports load time, milliseconds per substep, effective steps per second, and
resident artifact size. Real-time 10 FPS is a measurement target, not a promise;
correctness and provenance take priority.

## Failure behavior

The builder stops on:

- checksum mismatch;
- missing required columns;
- duplicate annotation body IDs;
- unexpected official neuron or edge counts;
- endpoints absent from the sorted body-ID index;
- non-positive structural weights;
- invalid CSR shapes or non-finite normalized weights.

Runtime loading stops on an incompatible schema, dataset, checksum, dynamics
identifier, shape, dtype, or count. Errors remain English and name the repair
command.

## Testing and acceptance

Small synthetic Feather fixtures prove filtering, ID indexing, polarity,
normalization, artifact round trips, and corruption rejection without requiring
the 1.1 GB source during unit tests. Engine parity tests compare compact and CSR
updates on the same small graph.

Milestone acceptance requires:

1. all existing tests pass;
2. the real build produces 166,606 retained neurons, 166,400 connected neurons,
   and 25,574,615 edges;
3. `brain-status` validates the generated artifact and pinned inputs;
4. a full-engine Experiment 1 smoke run reaches sensor-to-motor output;
5. a benchmark is recorded in `docs/status.md`;
6. no `world -> brain` or `brain -> world` dependency is introduced;
7. documentation clearly separates MaleCNS facts from dynamics assumptions.

## Later milestones

The gym will be Experiment 2 because it exercises natural visual, olfactory,
descending, and motor pathways. General reinforcement/plasticity follows after
the full engine is measured. Three.js then visualizes telemetry through a stable
transport boundary. Poker remains a later artificial task and must not be
presented as natural fly cognition.
