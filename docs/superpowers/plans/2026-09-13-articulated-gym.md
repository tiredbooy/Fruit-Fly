# Articulated Gym Implementation Plan

**Goal:** Real, neurally powered bench/curl repetitions with visible equipment
motion, recovery, and measured compact-network efficiency improvements.

**Architecture:** Extend Experiment 2 world mechanics and immutable telemetry.
Python owns every exercise transition; Three.js observes and interpolates.
Independent graph optimization and equipment mechanics can be implemented in
parallel with disjoint file ownership, then integrated with the observer.

**Tech stack:** Existing Python, unittest, aiohttp, TypeScript, Bun, Three.js.

**Spec:** `docs/decisions/0006-articulated-gym-equipment.md`.

## Global constraints

- No new biological IDs, classes, transmitters, or structural edges.
- No world behavior policy, scripted station seeking, or frontend motor commands.
- No new dependencies; preserve the user's dirty worktree; no commits requested.
- Browser UI Persian RTL; terminal and documentation English.
- New gym schema 3; preserve E1 schema 1 and read legacy gym schema 2.
- New work/reps require actual joint displacement; no elapsed-time rewards.

## Task 1: Equipment and physiology

Files: `world/equipment.py`, `world/gym.py`, `simulation/gym.py`,
`simulation/gym_signals.py`, `experiments/experiment_002.py`,
`frontend/gym_telemetry.py`, `frontend/gym_server.py`, matching Python tests,
and `docs/science/equipment.md`.

1. [ ] Add failing tests: zero drive produces zero reps/reward; loaded upward
   motion performs work; full return completes exactly one rep; three reps earn
   one reward; partial strokes cannot count; heavier load slows motion; fatigue
   recovers; occupied stations exclude another fly; removal releases grip.
2. [ ] Implement bounded substepped joint dynamics and per-fly exercise state.
   Populate actual bench/curl stations, using physical contact and existing
   neural motor output. Preserve the original resistance-lane API for E1-era
   regression tests. Handle long finite timesteps without skipping stroke ends.
3. [ ] Integrate actual per-set rewards with separate gym memory, food ingestion,
   bounded physiology and population lifecycle. Emit schema-3 contract from spec.
4. [ ] Run focused tests and finite actual-circuit 1/3/10-fly experiments. Record
   observed repetitions, sets, work and learning on/off without overstating them.

## Task 2: Compact network efficiency

Files: `brain/network.py`, focused brain tests,
`docs/neural-performance-2026-09-13.md`.

1. [ ] Profile actual pinned E1/gym circuit loops before edits.
2. [ ] Write equivalence and mutable-state isolation tests against original loop.
3. [ ] Cache static edge calculations/labels without changing arithmetic order.
4. [ ] Run covering tests and report repeated before/after timings with caveats.

## Task 3: Equipment scene, animation and observation

Files: `frontend/web/src/equipment-*.ts`, `gym-types.ts`, `gym-snapshot.ts`,
`gym-scene.ts`, `animated-fly.ts`, `fly-population.ts`, `fly-scene.ts`,
`gym-dashboard.ts`, `neuron-inspector.ts`, relevant tests, index and CSS.

1. [ ] Test schema-3 validation, legacy schema-2 parsing, bounded positions,
   nullable station identity, independent rig posing and no elapsed-time reps.
2. [ ] Render bench supports, bar/plates, dumbbell rack and articulated handles
   from server geometry. Use actual rig forelegs and measured joint position;
   keep observer-only camera controls and actual-body root transforms.
3. [ ] Show selected exercise, rep count and recovery from telemetry. Reuse
   neuron DOM rows without losing exact values, search, or keyboard focus.
4. [ ] Run Bun/TypeScript/build and actual desktop/mobile browser observation.

## Task 4: Integration, review and documentation

1. [ ] Run `make test`, `make data-status`, frontend tests/build, finite gym
   smoke runs and boundary checks. Stop all servers started for this task.
2. [ ] Inspect desktop/mobile and bench/curl motion, fix concrete defects as a
   batch, and obtain independent code/visual review.
3. [ ] Update README, AGENTS, architecture, status and design documentation with
   actual mechanics, commands, performance evidence and scientific limits.
4. [ ] Run `git diff --check`. Hand off `make gym FLIES=3`, no automatic commit.
