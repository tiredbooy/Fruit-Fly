# FlyBrain Lab Engineering Rules

## Project purpose

FlyBrain Lab is a from-scratch, inspectable fruit-fly neural simulation built
from the official MaleCNS connectome. The current milestone is Experiment 1:
one fly, one food source, hunger, smell, simple vision, locomotion, and
appetitive olfactory learning. The project also has an optional full-connectome
CPU backend. This is a neural-control simulation, not a claim of consciousness.

## MaleCNS provenance

- Biological neuron IDs, neuron types, cell classes, neurotransmitter calls,
  and synaptic weights must come from the pinned official MaleCNS release.
- Never copy IDs, circuits, source code, or model behavior from another fly-brain
  project.
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
- `frontend` observes telemetry only. It must never change simulation state.
- Persistent storage is loaded and saved at the application boundary, not from
  domain calculations.
- Never add logic equivalent to `if food is left: turn left` or
  `if hunger is high: seek food`.
- Keep compact and full-connectome engines behind the same `NeuralNetwork`
  boundary. Compact remains the default until a new experiment opts into full.

## Learning and memory

- Experiment 1 learning is appetitive DM1 odor association only.
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
