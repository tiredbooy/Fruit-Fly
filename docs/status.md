# Project Status

Last updated: 2026-09-13

## Current milestone

Experiment 1 runs one fly with a dynamic food source in a bounded two-dimensional
world. Food begins absent, respawns after random delays, expires, and may appear
far away or outside accessible bounds. The live English terminal and Persian
Three.js observatory show physical state, bilateral smell and vision, hunger,
named descending-neuron activity, motor output, reward, and persistent
association strength. Both interfaces can run on the compact circuit or the
full MaleCNS graph.

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
- A memory-mapped CSR artifact contains all 166,606 valid-superclass bodies,
  including 206 isolated bodies, and 25,574,615 valid neuron-to-neuron edges.
- `make brain-build`, `make brain-status`, `make brain-benchmark`, and
  `make run-full` manage the optional full backend. Compact remains the default.
- `make web` serves a responsive Three.js specimen chamber with live versioned
  telemetry; `make web-full` selects all 166,606 valid MaleCNS bodies.
- The browser can pause/resume the authoritative Python clock but cannot steer,
  feed, or inject neural activity.

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

The full graph was built and measured on the development machine on 2026-09-13:

```text
build time:          6.97 seconds
artifact size:       198.3 MiB
neurons:             166,606
connected neurons:   166,400
edges:               25,574,615
graph load:           0.0679 seconds
10 neural substeps:  0.1460 seconds
per neural substep:  14.596 ms
neural substeps/sec: 68.51
```

A five-step `run --brain full` smoke test completed successfully. Benchmark
results are machine-specific and should be remeasured after dependency, graph,
or dynamics changes.

Browser verification on 2026-09-13 covered 1440x1000 and 390x844 viewports:
live frames advanced, pause/resume froze and restarted the same Python clock,
WebGL rendered one canvas, mobile horizontal overflow was zero, and the browser
console contained no errors. Full-mode startup reported `backend: full` and
`dataset: male-cns:v1.0` through `/health`.

Final verification commands:

```bash
make test
make frontend-build
make data-status
make brain-status
make brain-benchmark
make help
```

## Known limitations

- Experiment 1 defaults to the compact circuit; full mode is opt-in.
- Neural state is a rate proxy rather than a conductance or spike model.
- Full-graph transmitter signs and rate equations are explicit modeling
  assumptions, not measured membrane physiology.
- Neuromodulators have zero fast-current sign in the full graph; dedicated
  modulatory pathways remain future work.
- Sensory activity reaches the configured descending neurons in full mode, but
  whole-graph incoming normalization makes current motor output approximately
  `10^-6`. Movement is therefore not visually meaningful until the gym milestone
  defines and validates a full-network calibration instead of inventing a gain.
- Vision begins at L2 and omits photoreceptor transduction.
- The DM1 channel is used as an ACV-like food-odor approximation.
- Learning supports one appetitive odor association only.
- Reward is produced by contact ingestion rather than gustatory and metabolic
  neural pathways.
- Learned memory changes odor salience through an explicit model adapter, not a
  fully reconstructed MBON-to-descending circuit.
- The simulator has no evidence of consciousness or subjective experience.
- The fly body and neural halo are procedural visual symbols, not anatomical
  reconstructions.

## Next milestone

The next implementation milestone is the fly-gym task protocol and benchmark
suite, followed by general learning across those tasks. Poker remains a later
research evaluation; it is not implemented.
