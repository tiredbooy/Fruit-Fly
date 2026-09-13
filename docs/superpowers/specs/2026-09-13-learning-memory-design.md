# Experiment 1 Learning, Memory, and Documentation Design

Date: 2026-09-13
Status: Approved

## Objective

Add persistent appetitive olfactory associative learning to Experiment 1 without
allowing the world layer to select behavior. The implementation must use only
official MaleCNS neuron identifiers, types, neurotransmitter calls, and edge
weights. It must also establish durable project documentation and simple
Makefile commands.

This feature does not create consciousness. It adds a bounded computational
model of one form of fly learning: associating the current DM1 food odor with
the reward produced by eating.

## Scientific Basis

The adult Drosophila mushroom body is a major site of associative learning.
Olfactory projection neurons activate sparse Kenyon-cell populations. Dopamine
neurons provide reinforcement, and plasticity at Kenyon-cell-to-mushroom-body-
output-neuron synapses stores learned odor value.

Experiment 1 will use these official MaleCNS classes:

- `ORN_DM1`: food-odor sensory population already used by Experiment 1.
- `DM1_lPN`: DM1 lateral projection neurons connecting odor input to Kenyon
  cells.
- `Kenyon_Cell`: the official annotation class used for mushroom-body intrinsic
  neurons.
- `PAM01(y5)`: official PAM dopaminergic neurons used as the positive reward
  population.
- `MBON01(y5B'2a)`: official mushroom-body output neurons receiving plastic
  Kenyon-cell input in a reward-relevant compartment.

Primary references:

- Li et al., "The connectome of the adult Drosophila mushroom body provides
  insights into function," eLife 2020, https://elifesciences.org/articles/62576
- Hige et al., "Heterosynaptic plasticity underlies aversive olfactory learning
  in Drosophila," Neuron 2015, and the circuit synthesis in the eLife article
  above.
- Jacob et al., "Dopamine-mediated interactions between short- and long-term
  memory dynamics," Nature 2024,
  https://www.nature.com/articles/s41586-024-07819-w
- Eichler et al., "The complete connectome of a learning and memory centre in
  an insect brain," Nature 2017.

The exact runtime IDs and weights remain data, not source-code assumptions.
They are selected deterministically from the pinned MaleCNS v1.0 release and
validated against its checksums.

## Model Assumptions

MaleCNS is a structural connectome; it does not supply a complete dynamical or
plasticity model. The following are explicit model assumptions:

1. Food contact produces a normalized positive reinforcement value. This is a
   physiological outcome, not a movement command.
2. Reinforcement activates the selected official `PAM01` population as a
   modulatory signal. Dopamine is not treated as an ordinary excitatory or
   inhibitory current.
3. Recently active Kenyon cells retain a decaying eligibility trace.
4. Coincident eligibility and PAM reward depress the corresponding official
   KC-to-MBON01 structural synapse multiplier, bounded by configured minimum and
   maximum values.
5. The mean learned depression produces a continuous appetitive odor-salience
   gain inside the brain adapter. It never emits a direct turn or movement
   command.
6. Experiment 1 stores only appetitive DM1 memory. Aversive, visual, episodic,
   consolidation, extinction, and multi-odor memories remain future work.

These assumptions must appear in user documentation, runtime metadata, and
tests. They must never be presented as measured MaleCNS physiology.

## Runtime Flow

```text
WORLD
  food contact -> ingestion amount
  odor field   -> left/right physical stimulus
        |
        v
SENSORS
  bilateral smell + simple vision
        |
        v
BRAIN ADAPTER
  hunger gain * learned odor-salience gain
        |
        +-> DM1_lPN -> sparse official KCs -> MBON01 response
        |                       ^
        |                       |
        |             PAM01 reward-gated plasticity
        |
        v
OFFICIAL SENSOR-TO-DESCENDING SUBGRAPH
        |
        v
MOTOR READOUT -> FLY BODY -> WORLD
```

The simulation orchestrator owns sequencing. `world` never imports `brain`, and
`brain` never imports `world`. Immutable signal objects cross the boundaries.

The order for each tick is:

1. Sample the physical sensors.
2. Apply hunger and learned salience inside the brain adapter.
3. Advance the network and decode descending-neuron activity.
4. Move the body and compute physical ingestion.
5. Convert ingestion to a reward signal.
6. Apply reward to the eligibility trace created by the preceding odor state.
7. Emit telemetry and persist a changed memory snapshot.

## Memory State and Persistence

Default path: `data/runs/experiment-001-memory.json`

The file is runtime state and remains git-ignored. It uses a versioned schema:

```json
{
  "schema_version": 1,
  "dataset": "male-cns:v1.0",
  "weights_sha256": "...",
  "model": "pam01-kc-mbon01-v1",
  "reward_events": 0,
  "total_reward": 0.0,
  "synapses": [
    {
      "body_pre": 0,
      "body_post": 0,
      "baseline_weight": 0,
      "multiplier": 1.0
    }
  ]
}
```

Loading rejects unknown schema versions, dataset/checksum mismatches, missing or
extra synapses, changed baseline weights, duplicate edges, non-finite numbers,
and out-of-range multipliers. It does not silently reset invalid memory.

Saving uses a temporary file in the same directory, flushes it, and atomically
replaces the destination. `--reset-memory` moves the previous file to a backup
before creating clean state so the operation is recoverable.

## Components

### Brain

- `brain/learning.py`: pure learning configuration, eligibility updates,
  reward-gated plasticity, and observable learning events.
- `brain/memory.py`: immutable memory records and JSON persistence validation.
- `brain/network.py`: applies per-edge multipliers while retaining official
  baseline weights.
- `brain/sensory.py`: calculates continuous hunger and learned salience gains;
  it does not select actions.
- `brain/circuit.py`: validates learning roles and official circuit provenance.
- `data/circuits/foraging-v1-learning.json`: derived official learning subgraph,
  selection metadata, and plastic edge declarations.

### Simulation

- `simulation/signals.py`: adds reward and learning telemetry DTOs.
- `simulation/loop.py`: sequences sensing, action, ingestion, reward, learning,
  and telemetry without containing learning equations.
- `experiments/experiment_001.py`: composes the learning system and its explicit
  parameters.

### Interfaces

- `frontend/console.py`: shows reward, eligibility, association strength,
  memory-file state, and plasticity events using English ASCII only.
- `main.py`: accepts `--memory-file` and `--reset-memory`, loads and saves memory,
  and reports actionable errors.
- `Makefile`: provides `run`, `run-fresh`, `test`, `data-status`, and `help`.

### Documentation

- `AGENTS.md`: repository-wide engineering and scientific rules.
- `README.md`: installation, quick start, commands, and limitations.
- `docs/architecture.md`: current dependency boundaries and runtime flow.
- `docs/science/learning-memory.md`: scientific evidence, exact selected
  populations, equations, and assumptions.
- `docs/status.md`: current behavior, verified state, known limitations, and
  next milestone.
- `docs/decisions/0001-learning-memory.md`: decision record and rejected
  alternatives.

## Makefile Contract

```text
make run          run indefinitely with ASCII terminal animation
make run-fresh    archive existing memory and run with clean memory
make test         execute the complete unittest suite
make data-status  validate pinned assets, neuron roles, and runtime edges
make help         show the available targets
```

The Makefile introduces no new build dependency beyond `make` and the existing
project virtual environment.

## Error Handling

- Missing raw MaleCNS assets: stop with the exact missing path.
- Invalid official ID, type, transmitter, or edge: fail before simulation.
- Unsupported dopamine use as fast signed current: reject circuit loading.
- Invalid memory file: fail with a specific English ASCII error.
- Persistence failure: keep the simulation state in memory, stop cleanly, and
  report the path and cause.
- `Ctrl+C`: save dirty memory, restore the terminal, and exit successfully.

## Testing

Tests are written before implementation and cover:

- deterministic official learning-circuit selection and validation;
- eligibility decay without reward;
- reward changes only eligible synapses;
- bounded plastic multipliers;
- learned salience changes continuously with memory strength;
- persistence round trip, atomic replacement, mismatch rejection, and reset
  backup;
- simulation ordering and absence of direct world-to-motor behavior;
- CLI parsing and ASCII-only renderer output;
- Makefile targets;
- architecture import boundaries;
- documentation existence and required sections.

Acceptance verification also runs a deterministic two-session experiment: the
first session trains at food, and the second session loads the saved synaptic
state and exhibits a stronger odor response than a clean-memory control under
the same sensory input.

## Alternatives Rejected

### Plasticity on Existing ORN-to-Motor Paths

This is smaller, but it incorrectly presents direct sensory-motor weight changes
as fly associative memory and omits the mushroom body.

### Coordinate or Event History

An episodic list of food positions is easy to persist, but it invites world
logic to query memory and directly steer the fly. It is not the requested neural
learning architecture.

### Full Mushroom-Body Simulation

Simulating all 4,075 Kenyon cells, all compartments, recurrent DAN/MBON loops,
consolidation, extinction, and multiple memory timescales is scientifically
interesting but exceeds Experiment 1 and would make validation harder. The
approved design keeps a deterministic official subgraph that can expand later.

## Documentation Maintenance Rule

Every material code change must update the documentation that describes it:

- behavior or project state -> `docs/status.md`;
- boundaries or data flow -> `docs/architecture.md`;
- scientific assumptions or neuron selection -> `docs/science/`;
- consequential design choice -> a decision record in `docs/decisions/`;
- commands or setup -> `README.md` and `Makefile`.

Code docstrings explain what each public module and non-obvious model object
does. Comments explain why a scientific or architectural choice exists; they do
not narrate obvious Python syntax.
