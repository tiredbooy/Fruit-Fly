# Experiment 2 articulated equipment

This document supersedes the resistance-lane equations in `gym.md` for the
default Experiment 2 composition. The original `ResistanceStation`,
`TrainingState.advance` and `move_under_load` APIs remain available and tested.
Experiment 1 is unchanged. These human-style motions are illustrative mechanics,
not measured insect biomechanics or evidence that flies understand a gym.

## Biological provenance and model assumptions

The pinned official MaleCNS runtime, food-learning and DM2 learning circuits
remain the source of all biological IDs, labels, transmitters and structural
weights. No new biological role is assigned to any neuron. The same descending
neuron readout produces `MotorDrive.forward` and `MotorDrive.turn`; the existing
food/gym sensory encoding and separate bounded memories remain in use.

Mapping forward motor output to foreleg force while a grip is physically engaged
is a model assumption. Contact attachment, posture, the upper-limit force
release, downward return, recovery time, continuous restraint, synthetic station odors, set rewards,
fatigue and fitness are also model assumptions. They are engineering choices,
not functional evidence that these descending neurons encode presses or curls.
The `world` package never imports `brain`, and does not choose a destination,
food target, turn, or exercise. Initial equipment contact and continued station
restraint are explicit experimental exposure, not learned station seeking.

## Geometry and setup

The arena remains 20 by 12 ground-plane model units. There are ten immutable
stations, `station-1` through `station-10`. For zero-based index `i`, a station and
its initially corresponding fly have:

```text
x = -6.4 + 3.2 * (i % 5)
y = -2 + 4 * (i // 5)
heading = 0.22 + 0.12 * i
```

Even indices are bench presses; odd indices are curls. Fly-1 initially touches
a bench press and fly-2 a curl. Initial hunger is still 0.42; initial neural
activity is zero. The first actual motor signal can engage the contact.

| Equipment | Load | Vertical travel | Contact radius | Body elevation | Pitch | Roll |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `bench_press` | 0.60 | 0.70 | 0.45 | 1.50 | 0 | pi |
| `bicep_curl` | 0.40 | 0.55 | 0.45 | 0.50 | 0.55 | 0 |

All lengths, loads and angles above are authored model values; angles are radians.
The root pose was calibrated to the existing displayed rig, whose thorax has a
native height around 0.725 and foreleg reach around 0.95. These are rendering
asset dimensions, not measurements of the connectome specimen. In the authored
rig's coordinates, local +X points forward, roll uses that axis, and positive
pitch about local +Z raises the head.

The matching observer uses bench cushion top around 0.40, bar base height 0.90,
and grips at forward 0.32 and lateral +/-0.55. The curl grips start at height
0.62 with lateral +/-0.50; their forward coordinate is
`0.45 + 0.15*sin(pi*q) - 0.10*q`. Each handle rises by `travel*q`. This geometry
keeps the authored forelegs within reach. It does not add a physical 3D arena or
measured limb segments to the neural model.

Each station emits `1 / (1 + squared_distance / 9)`. The two existing antenna
positions independently sample the strongest station field. Taking the maximum
keeps the synthetic cue in 0..1 as the number of stations changes. Food odors
and vision retain their existing independent sampling.

## Contact, dynamics and repetitions

`EquipmentFloor` owns station occupancy. A free fly with positive neural forward
output can grip only within the station's 0.45 contact radius, and only if no
other fly occupies it. The support then constrains the already-contacting root
to the station anchor and heading. That position correction is at most the
contact radius. There is no attraction force, navigation target, or coordinate
change to move a distant fly onto a station. Attachment does not produce work.

The scalar joint has normalized position `q` in 0..1 and velocity `v` in
normalized position per second. Positive physical displacement is `travel*dq`.
With model gravity 1, inertial mass equals the station load:

```text
capacity = (1 - 0.75*fatigue) * fitness
force = 6 * clamp(neural_forward, 0, 1) * min(1, capacity)
acceleration = (force - load) / (load * travel) - 3*v
v_next = v + acceleration*dt
q_next = clamp(q + v_next*dt, 0, 1)
positive_work = load * travel * max(0, q_next - q)
```

The joint uses deterministic semi-implicit integration with substeps no longer
than 0.01 seconds. At the upper stop, velocity is zeroed and the grip actuator
releases its upward force. Gravity and damping then return the joint to the
bottom. Only that full upper-stop-to-bottom return increments a repetition.
A partial upward stroke returning to the bottom does not count. Resting, turning,
walking, occupied-equipment contact and wall contact earn no exercise work or sets.
Heavier loads have greater downward force and inertia and move less under the
same neural drive. No rep is advanced by an animation or an elapsed-time timer.

Three completed repetitions make a set. In default Experiment 2, completion
racks the joint, resets `rep_in_set`, and starts a two-second recovery while the
station retains its exclusive grip and supported body pose. The next set becomes
available after recovery, but its upward stroke still requires positive neural
motor output. The apparatus therefore forces attendance, not work. An explicit
population removal releases the grip and uses the existing four-second detached
recovery. A zero motor output cannot start an otherwise resting lift.

The normalized set progress shows half a repetition for the upward stroke and
half for the downward stroke. During lifting it is `(rep_in_set + q/2)/3`;
during lowering it is `(rep_in_set + 1 - q/2)/3`.

## Physiology, rewards and population lifecycle

At each physics substep:

```text
effort = min(1, positive_work / (0.6*dt))
fatigue = clamp(fatigue + 0.30*positive_work - 0.025*dt*(1-effort), 0, 1)
fitness = min(1.5, fitness + 0.005*new_sets)
```

Positive work accumulates even for incomplete strokes, but only complete sets
produce a 0.9 reward. The gym learner receives exactly one reinforcement event
per newly completed set; a frame's reward is a bounded pulse indicating that at
least one set completed during that frame. Partial work cannot manufacture a set
by crossing a cumulative-work threshold. A complete bench set performs 1.26 work
units; a complete curl set performs 0.66. Kinetic energy and damping losses are
not added to the reported load-lifting work; this is not a full metabolic model.

Unloaded body motion contributes to `training.distance`, but no exercise work.
The docking position correction is excluded from locomotor distance. Food intake
retains the existing ground-plane radius check, and additionally requires the fly
to be free of a supported exercise grip; a fly on a bench cannot ingest food
through the ground projection of its elevated pose. Metabolism and hunger bounds
are unchanged. Additional exercise hunger remains `0.002*effort*dt`.

Coarse simulation ticks are subdivided into at most 0.1-second sensory, neural,
food and reward updates, with equipment physics subdivided further. A 20-second
tick therefore cannot freeze its initial neural drive through an entire workout
or omit intermediate set rewards. Timestep dependence below this upper bound
remains: the existing neural network is discrete and not calibrated to a physical
continuous-time rate. Legacy lane-only `GymSimulation` construction retains its
old stepping behavior.

Population reduction releases occupied stations at the application boundary,
racks a partially raised weight without rewarding its unfinished stroke, resets
the partial set and preserves lifetime completed-repetition/set counters. A
removed fly retains its body position, memories, fatigue and network state; its
recovery timer resumes only when that identity is active again. The release is
an explicit setup operation and does not advance the clock. No workout state is
persisted across process restarts. Existing per-fly food/gym memory identities and
atomic storage are retained; learned gym cue associations can therefore carry
over from the earlier resistance-lane experiment.

Removing an already free or recovering fly leaves its exercise state unchanged.
In particular, removing and readding an unattached identity while paused does not
restart its recovery interval. Only an actual held grip triggers the release
operation and its new recovery interval.

## Observation and executable evidence

The new gym server emits schema 3 in hello, health and `gym_frame`. Hello carries
the exact immutable station geometry under `equipment`; the legacy `station`
object remains for compatibility. Every fly has an immutable `exercise` snapshot
with station identity, kind, phase, joint position/velocity, repetitions,
completed sets, repetition within the set, recovery time, elevation, pitch and
roll. Nested neural/body frames still mean schema 1. Commands remain pause/resume
and validated population setup. Pausing stops all joint and physiology updates;
the observer receives no authority to synthesize repetitions.

During inter-set recovery, `station_id` and `kind` remain non-null because the
fly is still physically attached. Detached recovery after population removal
retains null station/kind. Schema 3 accepts both recovery states.

A legacy lane-only `GymSimulation` constructed with `equipment=None` continues
to serve schema 2 consistently in hello, health and initial/live frames. Its
hello omits `equipment`, and its per-fly frames omit `exercise`. Default
`create_gym` compositions have equipment and continue to serve schema 3.

`tests/world/test_equipment.py` checks zero-drive behavior, actual positive work,
full returns, exactly three repetitions per reward, partial-stroke rejection,
heavier loads, fatigue recovery, physical contact, exclusive occupancy, removal,
continuous attached recovery, subsequent contact and long finite ticks. Existing
lane tests still pass.
`tests/simulation/test_gym.py` uses the real pinned circuits to check independent
state, continuous assignment, learning disabled/enabled, removal, ground-food
contact and coarse/fine-step equivalence. HTTP/WebSocket tests exercise schema 3,
unchanged nested schema 1, pause, population changes and reconnect snapshots.

Initial integrated Python verification on 2026-09-13: `make test` passed all 122 tests in
86.958 seconds, including official manifest reproduction, neural-loop
equivalence and Experiment 1 regression checks. `make data-status` validated the
92 gym runtime and 104 gym-learning edges against the official assets.
`git diff --check` was clean and direct brain/world cross-import searches found
no matches. Local HTTP/WebSocket tests used permission to open loopback sockets;
their test servers shut down normally.

After the targeted review fixes for paused recovery preservation and legacy
schema selection, all eight covering population-lifecycle and gym HTTP/WebSocket
tests passed, including the two added regressions.

Continuous-protocol verification on 2026-09-13 passed all 126 Python tests and
all 35 browser unit tests. The strict TypeScript production build passed, and
`make data-status` revalidated 151,856,684 connection rows, 92 gym runtime edges,
and 104 gym-learning edges. A real 390-pixel browser rendered the ten-fly gym
through the reported WebGL2 fallback. Headless Chrome could not initialize its
native WebGPU swap chain; the information interface remained live as required.

## Pre-continuous-protocol trajectory measurements, 2026-09-13

Fresh seed-7 runs used populations 1, 3 and 10, learning disabled and enabled, at
0.1 seconds per tick. Each ran 1800 ticks, with observations at ticks 600 and
1800. Both learning modes had the following counts and load work at both times:

| Population | Completed sets per fly | Repetitions per fly | Positive work per fly |
| --- | --- | --- | --- |
| 1 | 2 | 6 | 2.52 |
| 3 | 2, 2, 2 | 6, 6, 6 | 2.52, 1.32, 2.52 |
| 10 | 2, 2, 2, 1, 1, 1, 1, 1, 1, 1 | 6, 6, 6, 3, 3, 3, 3, 3, 3, 3 | 2.52, 1.32, 2.52, 0.66, 1.26, 0.66, 1.26, 0.66, 1.26, 0.66 |

All initial contacts occurred at tick 1. Fly-1 naturally contacted station-3
at tick 161, fly-2 station-4 at tick 141, and fly-3 station-5 at tick 181. Those
stations had already been released by their original occupants in the larger
populations. The remaining seven flies used only their initial station. No
additional equipment visit occurred between tick 181 and tick 1800.

Every fly had nonzero actual root displacement in every one of the final 100
ticks at both checkpoints, using a 1e-8 distance threshold. Thus the measured
inactive fraction was zero, but this is not evidence of sustained exercise:
the trajectories converged toward the arena edge and continued moving along it.
At tick 600 the ten flies were around x=9.95, y=-4.7. At tick 1800 the enabled
ten-fly run had positions x=1.99..7.80, y=-5.37..-3.77, and cumulative distances
68.74..82.38 across the measured enabled runs. Wall clipping still shapes the
paths; no wall-sensing or body-collision circuit was added.

Peak sampled fatigue was 0.23659 and final fatigue was zero for every fly.
Enabled gym association for flies 1..3 reached approximately 0.0104980,
0.0104932 and 0.0104982; the other seven were approximately 0.005426..0.005431.
Disabled associations remained zero. By tick 1800, populations 1 and 3 each
consumed one food source in either learning mode; ten flies consumed one with
learning disabled and two with learning enabled. In the enabled ten-fly run,
fly-4 and fly-5 consumed those sources and acquired food associations around
0.001175 and 0.001181, independent of their gym memories.

The enabled ten-fly 1800-tick loop took 7.425 seconds in one headless local
sample, excluding loading and composition and including measurement overhead.
This is not a browser FPS benchmark or an isolated performance comparison.
These measurements describe the earlier release-after-set behavior. Learning did
not improve set counts in these runs. The evidence supports loaded
joint motion, recovery, some actual station reuse, and work-triggered odor
association. It does not establish long-term equipment preference, biological
exercise learning, or a guaranteed return to training. Broader seeds, calibrated
sensory feedback, collision mechanics and continuous-time neural dynamics remain
unvalidated.

## Continuous forced-training measurement, 2026-09-13

A fresh seed-7 run with ten flies and learning enabled ran for 1000 ticks at
`dt=0.1`. Bench flies completed 7 sets each; curl flies completed 10 sets each.
All ten retained their original `station-1` through `station-10` assignments,
all ten remained in an exercise phase, and every locomotor distance stayed zero.
Final fatigue was 0.642..0.839 for bench flies and 0.037..0.077 for curl flies.
This demonstrates sustained operation of the imposed apparatus protocol. It is
not evidence of voluntary exercise, exercise preference, addiction, or biological
training behavior.
