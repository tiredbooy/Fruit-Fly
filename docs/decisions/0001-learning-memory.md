# Decision 0001: Mushroom-Body Associative Memory

Date: 2026-09-13
Status: Accepted

## Context

Experiment 1 needed learning that persists across runs while preserving the rule
that the world cannot directly choose fly behavior. The system already had an
official ORN_DM1-to-descending circuit, hunger modulation, and food-contact
ingestion. It had no plasticity, reward signal, or persistent neural state.

## Decision

Implement appetitive DM1 odor memory as PAM01-gated plasticity on a deterministic
official DM1_lPN-to-Kenyon-cell-to-MBON01 subgraph.

The memory file stores only versioned multipliers for exact official
KC-to-MBON01 baseline edges. Food ingestion creates reward after body physics;
reward changes eligible brain synapses but never creates a movement command.
Learned association continuously increases odor salience inside `BrainAdapter`,
after which the existing MaleCNS-derived network and motor readout determine
movement.

Persistence belongs to `main.py` through `MemoryRepository`. Learning equations
remain pure brain-domain transitions with no file I/O.

## Why

- It uses the biological circuit class most strongly associated with fly
  olfactory learning instead of labeling arbitrary motor adaptation as memory.
- Every biological identifier and structural edge can be validated against the
  pinned MaleCNS files.
- It keeps reward, plasticity, persistence, and behavior responsibilities
  separate and testable.
- A compact subgraph is understandable now and can expand to more compartments
  later.
- Persistent edge multipliers can be inspected, compared, reset, and migrated.

## Alternatives rejected

### Direct ORN-to-motor plasticity

This would be smaller but would bypass the mushroom body and misrepresent a
sensor-to-motor gain adjustment as associative memory.

### Coordinate or event-list memory

Remembering food coordinates would make it tempting for world or controller
logic to steer directly toward a known location. It would violate the required
neural control loop.

### Full mushroom-body model

All 4,075 Kenyon cells, all MB compartments, recurrent DAN/MBON loops,
consolidation, and extinction exceed Experiment 1. Adding them together would
make model assumptions difficult to isolate and verify.

## Consequences

Positive consequences:

- The fly acquires a persistent, inspectable association from experience.
- No neuron ID or structural connection is invented.
- The memory format fails safely when data or circuit versions change.
- The terminal can show acquisition as it happens.

Costs and limitations:

- Plasticity parameters and eligibility dynamics are model assumptions.
- MBON01-to-action expression is represented as continuous odor salience rather
  than a complete official downstream circuit.
- One DM1 association cannot represent general learning or memory.
- A future memory schema change will require an explicit migration or reset.
