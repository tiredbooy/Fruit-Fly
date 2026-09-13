# FlyBrain Lab Engineering Rules

## Project purpose

FlyBrain Lab is a from-scratch, inspectable fruit-fly neural simulation built
from the official MaleCNS connectome. Experiment 1 is preserved:
one fly, one food source, hunger, smell, simple vision, locomotion, and
appetitive olfactory learning. The project also has an optional full-connectome
CPU backend. Experiment 2 adds a compact 1-10 fly bench-press/dumbbell gym,
separate food/gym learning, and measured anatomical observation. This is a
neural-control simulation, not a claim of consciousness.

## MaleCNS provenance

- Biological neuron IDs, neuron types, cell classes, neurotransmitter calls,
  and synaptic weights must come from the pinned official MaleCNS release.
- Never copy IDs, circuits, neural/control source code, or model behavior from
  another fly-brain project. The user explicitly authorized visual asset and
  rendering reference reuse from their fly-escape project; record that narrow
  provenance exception without importing its brain, behavior, or datasets.
- Pin every official source URL and SHA-256 checksum in
  `data/malecns/<version>/source-manifest.json`.
- Validate every selected runtime edge against the official weights asset.
- Store evidence URLs and deterministic selection rules with circuit manifests.
- Never silently replace an unknown transmitter polarity with an assumed sign.
- The full graph uses the official valid-superclass filter: keep nonempty
  superclass values that do not contain `tbc`, and retain isolated valid bodies.

## Scientific honesty

- Do not invent a neuron ID, type, class, transmitter, or structural edge.
- A mathematical neuron, plasticity, sensor, body, or environment model may
  require assumptions. Label each assumption in the circuit manifest and in
  `docs/science/` before presenting it as behavior.
- Distinguish structural evidence, functional evidence, and model assumptions.
- Do not describe telemetry as thoughts, feelings, awareness, or consciousness.
- Keep unsupported biological claims out of names, UI text, and documentation.

## Architecture boundaries

The continuous dependency and control flow is:

```text
world -> immutable sensory signals -> brain -> immutable motor signals -> world
                                     ^
                                     |
                         ingestion reward and memory
```

- `world` owns physical geometry, odor fields, food contact, body mechanics,
  and physiology. It must never import `brain` or choose behavior.
- `brain` owns sensory encoding, neural dynamics, neuromodulation, plasticity,
  memory state, and motor readout. It must never import `world`.
- `simulation` owns immutable boundary signals and loop sequencing.
- `experiments` composes concrete configurations without hiding assumptions.
- `frontend` observes telemetry. Explicit commands are pause/resume and, only in
  Experiment 2, validated population setup. It never chooses fly behavior.
- Persistent storage is loaded and saved at the application boundary, not from
  domain calculations.
- Never add logic equivalent to `if food is left: turn left` or
  `if hunger is high: seek food`.
- Keep compact and full-connectome engines behind the same `NeuralNetwork`
  boundary. Compact remains the default until a new experiment opts into full.

## Learning and memory

- Experiment 1 learning is appetitive DM1 odor association only.
- Experiment 2 adds synthetic gym-odor association through validated DM2 paths.
  Preserve separate per-fly food/gym memory and eligibility. Reward arises only
  from newly completed physical work, never standing on a station or elapsed time.
- Bench/curl sets require three full loaded up/down repetitions. Positive joint
  travel supplies work; partial strokes cannot award sets. Keep physical grip
  occupancy exclusive and release it on population removal without free reward.
- Default Experiment 2 uses an explicit continuous-training apparatus: an active
  fly remains restrained at its assigned station during two-second inter-set
  recovery. This is imposed experimental setup, not learned exercise choice.
- The descending-drive-to-foreleg actuator, grip, range reflex and support poses
  are model assumptions, not new biological exercise functions. Preserve their
  documentation in circuit metadata and `docs/science/equipment.md`.
- Food ingestion may produce a PAM01 reward signal; it may not directly produce
  movement.
- Store memory as bounded multipliers on official KC-to-MBON01 edges.
- Keep dopamine modulatory; do not treat it as ordinary fast excitatory current.
- Version persistent memory and bind it to dataset, weights checksum, model, and
  exact plastic-edge set.
- Reject incompatible or corrupt memory rather than silently resetting it.
- Save atomically. User-requested reset must keep a recoverable backup.

## Code quality and testing

- Use Python type hints and focused modules with one clear responsibility.
- Prefer immutable dataclasses for values crossing package boundaries.
- Write a failing test first for every behavior change, observe the failure,
  implement the minimum change, and run the complete suite afterward.
- Preserve existing APIs unless an approved design explicitly changes them.
- Do not add dependencies when the standard library or existing packages work.
- Do not refactor unrelated code.
- Run `make test`, `make data-status`, and `git diff --check` before completion.
- For full-engine changes also run `make brain-status`, `make brain-benchmark`,
  and a finite `main.py run --brain full` smoke test.
- Verify that no import crosses directly between `brain` and `world`.

## Terminal interface

- All terminal-visible text must be English. Keep borders, meters, and labels ASCII.
- The fly glyph is intentionally the `🪰` emoji at the user's request. Use the
  automatic `F` fallback for terminals that cannot encode it.
- Restore cursor visibility and terminal state after completion or `Ctrl+C`.
- Show measured simulation state; never fabricate narrative thoughts.

## Browser observatory

- Browser UI text is Persian and right-to-left; official labels, IDs, dataset
  names, and technical mode names stay unchanged.
- Python owns the simulation clock, state, and persistence. The browser receives
  versioned JSON telemetry through the same-origin `/ws` endpoint.
- Browser commands are limited to pause/resume plus approved 1-10 population
  setup in gym schema 3 (the browser also reads legacy schema 2). Never add
  steering, feeding, or neural injection.
- Three.js geometry is a visualization. Anatomical soma points must use our
  pinned MaleCNS measurements. No invented locations, edges, or spike animation.
  Distinguish received-zero, received-positive, and unobserved points.
- Keep the information panel functional when WebGL is unavailable. Preserve
  keyboard focus, live connection status, reduced motion, and narrow layouts.
- Run `make frontend-build` plus a real-browser desktop/mobile check after UI
  changes.
- Prefer WebGPU with Three.js WebGL2 fallback and report the actual initialized
  backend. Keep telemetry running independently of asynchronous model loading.
- Imported visual models require a source, license, attribution, checksum, and
  documented transformations. The current rig is a user-authorized authored
  fly-escape asset, with no supplied public redistribution license; do not invent
  one. The previous licensed female CT body remains separately attributed.
  Neither is the male connectome specimen or measured locomotor biomechanics.
- Clone skeletons per fly, share geometry, and sample walking from actual
  displacement and feeding from ingestion. Never play a flight clip without
  Python flight state. Observer animation cannot move the physical root.
- Equipment geometry and foreleg grip targets must share received station/joint
  state. Do not use render time to cycle weights or increment reps. Keep actual
  elevated support poses separate from ground locomotion; no food intake through
  an elevated fly's ground projection. Keep rig/pose limitations explicit.
- Optimize neural updates only with original-loop equivalence and measured
  timings. Reuse received-neuron rows without dropping zero/tiny readings.
- Orbit/follow controls manipulate the observer only. The 3D arena depicts
  both experiments' ground plane; new physical dimensions require explicit Python
  physics and sensor work.
- Fly-eye view is an approximate observer camera, not biological compound-eye
  rendering. It must never change the vision signal or steer the body.
- Neuron inspection must use received official IDs, labels, and actual activity.
  Scope counts to the received subset; do not imply a whole-brain count, invented
  anatomical positions, or spikes. Preserve zero readings and small nonzero values.

## Documentation maintenance

Every material change must update the matching documentation in the same task:

- Setup, commands, or user workflow: update `README.md` and `Makefile`.
- Package boundaries or runtime flow: update `docs/architecture.md`.
- Scientific evidence, neuron selection, or model assumptions: update
  `docs/science/`.
- Current behavior, verification, limitations, or next work: update
  `docs/status.md`.
- Consequential architectural choice: add or update a record in
  `docs/decisions/`.

Public modules and non-obvious model objects need concise docstrings. Comments
must explain why a scientific or architectural choice exists, not narrate
obvious Python syntax.

## Approval scope

One explicit approval authorizes the complete scoped design and its normal
implementation steps. Do not repeatedly request approval for steps already
covered. Ask again only if new information requires a materially different
architecture, destructive action, external publication, or broader scope.

## Runtime data

- Official raw assets live under `data/raw/` and remain git-ignored.
- Per-run state and learned memory live under `data/runs/` and remain
  git-ignored.
- Generated full-graph arrays live under `data/processed/`, remain git-ignored,
  and must be reproducible with `make brain-build`.
- Reproducible manifests, checksums, selection rules, and compact derived circuit
  declarations are tracked in git.
- Never commit private data, secrets, temporary files, or machine-specific paths.
