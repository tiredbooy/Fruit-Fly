# Articulated gym equipment

Status: implemented; verification and limitations in `docs/status.md`, 2026-09-13.

## Request and scope

Extend the approved Experiment 2 gym with usable bench presses and dumbbell
curls, visible muscle/equipment motion, recovery and progress, and smoother
neural observation. Preserve Experiment 1 and the existing food/gym memories.
This is an extension of the existing brain/body/observer boundaries, not a
general physics engine or new biological circuit.

## Control and physics

Use the existing official descending-neuron motor readout to power a
dimensionless foreleg actuator when the body physically contacts an available
station. A bounded joint models lifting against load and gravity, with damping,
range stops, and a release at the upper limit. The weight must return to the
bottom to complete a repetition. Three full repetitions complete a set.
Positive lifting work, not animation time, contributes to fatigue and energy
use. Partial strokes, resting, occupied stations, and wall contact cannot award
sets. Body and equipment state are authoritative Python values.

Default Experiment 2 is a continuous forced-training protocol. A completed set
racks the joint but retains the exclusive grip and supported pose for a
two-second recovery, after which neural motor output can power the next set. The
apparatus forces attendance but supplies no lifting work, repetitions, or reward.
Initial assignment and continued restraint are explicit experimental setup, not
evidence that flies have learned to seek equipment. Food seeking remains the
same sensory/brain loop. No fake thoughts, invented neurons, or frontend steering
are introduced.

The foreleg actuator, grip, range reflex, recovery, bench posture, and synthetic
odor cues are engineering assumptions. MaleCNS descending neurons are not
claimed to encode bench presses or bicep curls. Fitness is bounded model
adaptation; appetitive DM2 learning remains odor association, not demonstrated
exercise preference or addiction. Physical constants and limitations belong in
`docs/science/equipment.md` alongside executable tests.

## Observation contract

New gym servers use schema 3. Experiment 1 stays schema 1. The new browser also
accepts old schema-2 gym messages. Commands remain pause/resume and population
setup only. Nested per-fly neural/body frames retain their schema-1 meaning.

Schema-3 hello adds `equipment`, an array of up to ten stations:
`{id, kind, x, y, heading, load, travel, grip_radius}`. Kinds are
`bench_press` or `bicep_curl`. Coordinates and heading use the existing world
frame. `travel` is the positive vertical stroke length in world model units.

Each schema-3 fly adds `exercise`:
`{station_id, kind, phase, joint_position, joint_velocity, repetitions,
completed_sets, rep_in_set, recovery_remaining, body_elevation, body_pitch,
body_roll}`. Nullable station/kind identify an unattached fly. Phase is `free`,
`lifting`, `lowering`, or `recovery`; recovery may be attached between sets or
unattached after population removal. Position is normalized 0..1; velocity is
normalized position/second; counts are nonnegative integers; rep_in_set is 0..2.
Pose values are physical model outputs in world units/radians.

The browser positions equipment and flies from this contract. It interpolates
received poses without extrapolating new reps. An independently cloned fly
skeleton reaches the actual weight handles, with joint phase controlling pose.
Paused simulations freeze workout motion. Missing graphics retain numeric
observations. Population removal must release any occupied equipment safely.

## Performance

Optimize repeated graph work while preserving update order, snapshots, and
independent fly state. Compare against the original compact loop using the
pinned circuits. Retain all received neuron readings, including tiny/zero
values; reuse DOM rows and buffers rather than discarding neural evidence.
No dependency additions, artificial FPS claims, or full-brain calibration
changes are part of this task.

## Trade-offs

An articulated, deterministic scalar joint is testable and inexpensive for ten
flies. A general rigid-body engine would add dependencies and substantial
collision/biomechanics work without making the neural assumptions more valid.
Human-scale gym motions are deliberately illustrative and are not insect
biomechanics. Publicly downloaded equipment is unnecessary: simple authored
Three.js machinery can match the Python joint geometry exactly.
