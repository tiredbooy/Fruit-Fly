# Gym and visual neural simulator implementation

Spec: `docs/decisions/0005-gym-and-fly-observation.md`, plus the user's request
for an anatomical activity display and animated fly using their fly-escape
repository as a visual reference. The gym architecture is already approved.

## Global constraints

- Preserve Experiment 1, its schema 1 protocol, and existing memory files.
- Python is authoritative. World geometry never chooses behavior; actual
  sensory input -> official MaleCNS circuit -> descending output -> body motion.
- All biological identities, connections, and soma positions come from our
  checksum-pinned MaleCNS assets. No fly-escape brain/control code or data reuse.
- Gym odor mapping, fatigue, fitness, reward, and learning equations are explicit
  model assumptions, not feelings, consciousness, measured dopamine, or addiction.
- One to ten independent flies share immutable circuit data. Count changes are
  validated at a tick boundary. Removed flies retain their memory.
- No new dependencies. Browser text Persian; terminal English. Existing dirty
  changes are preserved. Do not commit, publish, or alter the reference project.
- Use tests before behavior changes, actual browser verification after UI work,
  and document implementation, equations, provenance, limitations, and commands.

## Task 1: Python gym engine and versioned application boundary

Implement `world/gym.py`, gym physiology, `simulation/gym.py`,
`experiments/experiment_002.py`, second-channel circuit/learning composition,
gym protocol/server integration, CLI and Makefile targets, focused tests and
`docs/science/gym.md`. Keep responsibilities in focused modules.

1. Reproduce the official DM2 preflight in
   `.superpowers/sdd/gym-cue-provenance/analyze_dm2.py` (read-only provenance
   analysis, not a substitute for validation). Pin a reproducible compact gym
   circuit adding actual DM2 routes to the existing motor outputs. Validate
   source IDs, labels, transmitter calls, and edges. Generalize channel-specific
   learning without changing DM1 default or Experiment 1 memory identity. Separate
   food and gym eligibility/memory with actual official PN/KC/MBON edges.
2. Model one resistance-walking lane, distinct gym odor field, food and hunger.
   Body displacement under load earns work; no displacement earns no work, and
   only newly completed work sets earn a bounded gym reward. Fatigue reduces
   mechanical capacity; low work permits recovery. Fitness increases from actual
   training. Never choose steering, eating, training, or resting in the world.
   Initial placement near/on the lane is an explicit experimental condition.
   Learning modulates sensory gain, never directly sets motor output.
3. Maintain stable `fly-1` through `fly-10` identities and independent neural,
   physiological, and memory state. Preserve removed flies in a bounded bank.
   A count update accepts only integers 1..10, not bool/float/string/NaN. Apply
   changes on the next clock tick even when paused, without advancing physics.
   Persist per-fly food/gym memories at the application boundary in a separate
   Experiment 2 directory. Corrupt memory fails clearly; no silent resets.
4. Add `main.py gym` (headless finite run) and `main.py gym-web`; Makefile
   `gym`, `gym-run`, with `FLIES` default 1. Existing `web` and `run` unchanged.
   Gym is compact initially; reject unsupported full gym explicitly. No
   dependencies. Document all new commands and options in the report.
5. Wire contract for frontend (coordinate units same as current arena):
   `hello` schema 2 adds `experiment: "gym"`, `population: number`, and
   `station: {x,y,width,height,resistance}` to existing hello fields.
   `gym_frame` schema 2 has `step`, `elapsed`, `flies` array; each entry is
   `{id: string, frame: <unchanged schema-1 FrameMessage shape>, training: {
   set_progress, sets, effort, fatigue, fitness, reward, association_strength,
   total_work, distance}}`. All training values are finite; progress, effort,
   fatigue, reward, association_strength bounded 0..1, sets integer >=0;
   fitness >=1, total_work and distance >=0. `distance` is cumulative actual
   ground displacement, used for deterministic walk animation. Nested frame
   retains its real food, hunger, neural active IDs/labels/rate-proxy values.
   New command `{type:"set_population",count: number}` only on gym server.
   Reply `{type:"population",count:number}` only after application. Existing
   pause/resume and same-origin/size validation remain. Errors use existing
   error shape with Persian browser text. Send initial population immediately
   and current cached frame to reconnects. Keep payload bounded.

Acceptance: test zero-motion/no repeated reward, resistance/fatigue effects,
new-set reward, separate channel learning and persistence, count validation,
paused tick application, deterministic multiple flies, real official IDs/edges,
schema 1 regression, gym web integration. Run a real finite gym with learning
on and off; report measured outcomes, not a guaranteed improvement.

## Task 2: Reusable animated visual fly and anatomical neuron display

Root implements frontend asset/geometry work while Task 1 is delegated.
Use the user's authored rigged visual model from fly-escape only; record source
revision, SHA256, supplied-authorized-local-reuse status (not an invented public
license), rig, axis and visual-scale transformations. Retain old CT attribution.
Use SkeletonUtils for independent rigs and shared geometry. Animate walking from
actual cumulative distance, feeding from actual ingestion, idle still; pause
freezes animation. Do not infer airborne flight from a fly animation clip.
Actual flight physics is outside the approved ground model unless user adds it.

Export our own pinned MaleCNS soma positions with actual body IDs, valid
superclass filtering, missing/nonfinite coordinates omitted, uniform centering
and scaling, provenance and counts. Display a rotatable point cloud with actual
received activity mapped by body ID; unobserved differs from received zero.
No invented spikes, anatomical positions, connections, or whole-brain active
count. Keep exact numeric inspector as secondary detail. Failure to load anatomy
keeps numeric telemetry available. Render only when needed; bounded GPU buffers.
Tests cover measured coordinate handling, ID mapping, motion pause/distance,
cloning isolation, failure handling, stale/missing data and cleanup.

## Task 3: Gym UI integration, verification and documentation

Add a Persian fly-count form and selected-fly control using existing semantic
control patterns. Consume schema 2 with strict validation and retain schema 1.
Render shared gym lane/food and 1..10 animated bodies from actual telemetry;
camera follows selected fly, eye mode hides only selected body. Populate the
neuron display and measured training curve from selected fly records, with
bounded per-fly history and clear empty/loading/error/disconnect states.
Never send steering commands. Preserve instruments if renderer/model fails.

Run Python/Bun tests, strict TypeScript/build, official data validation,
finite gym and learning-disabled comparison, actual browser desktop/mobile,
count changes 1->10->1, selection, pause, eye camera, anatomical highlighting,
independent walking animation, reconnect and renderer failure. Update AGENTS,
README, architecture/status/scientific docs and decision 0005 to reflect reality.
Independent task and final code reviews must cover actual diffs and evidence.
