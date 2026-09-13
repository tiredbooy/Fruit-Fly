# Project Status

Last updated: 2026-09-13

## Current milestone

Experiment 1 runs one fly with a dynamic food source in a bounded two-dimensional
world. Food begins absent, respawns after random delays, expires, and may appear
far away or outside accessible bounds. The live English terminal shows physical state, bilateral smell and
vision, hunger, named descending-neuron activity, motor output, reward, and
persistent association strength.

The renderer uses a fly emoji for the body. Its status line reports `WAITING FOR
FOOD` while absent and `FOOD OUT OF REACH` for an outside-arena spawn.

## Implemented behavior

- Official MaleCNS v1.0 annotations, weights, and transmitter assets are pinned
  by URL and SHA-256.
- A 66-edge official sensor-to-descending circuit drives forward motion and
  steering through DNp09, DNa01, and DNa02 roles.
- Hunger increases with time, decreases during ingestion, and continuously
  changes odor response.
- An official DM1_lPN-to-Kenyon-to-MBON01 circuit tracks odor eligibility.
- Food contact activates official PAM01 reward identity and depresses eligible
  KC-to-MBON01 multipliers.
- Learned memory is atomically saved and restored across program runs.
- `make run`, `make run-fresh`, `make test`, and `make data-status` are available.

## Verified situation

The deterministic 600-step, 30 FPS smoke scenario produced:

```text
reward events:        34
total reward:         34.0
minimum multiplier:  0.396999
association strength on next process: 0.074
```

This demonstrates acquisition and cross-process persistence. It does not prove
biological accuracy beyond the explicitly cited structural and functional
constraints.

Final verification commands:

```bash
make test
make data-status
make help
```

## Known limitations

- Experiment 1 uses a compact selected circuit, not all MaleCNS neurons.
- Neural state is a rate proxy rather than a conductance or spike model.
- Vision begins at L2 and omits photoreceptor transduction.
- The DM1 channel is used as an ACV-like food-odor approximation.
- Learning supports one appetitive odor association only.
- Reward is produced by contact ingestion rather than gustatory and metabolic
  neural pathways.
- Learned memory changes odor salience through an explicit model adapter, not a
  fully reconstructed MBON-to-descending circuit.
- The simulator has no evidence of consciousness or subjective experience.

## Next milestone

The next scientifically coherent expansion is multiple distinguishable odor
channels with acquisition, extinction, and a clean-memory control. That work
must select additional sensory populations from official annotations and must
not reuse DM1 IDs for unrelated odors.
