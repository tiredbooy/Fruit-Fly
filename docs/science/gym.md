# Experiment 2: synthetic odor association and resistance walking

## Structural evidence

All biological identities, labels, transmitter calls and edge weights come from
the pinned official MaleCNS v1.0 assets in
[`source-manifest.json`](../../data/malecns/v1.0/source-manifest.json).
The three source URLs and SHA-256 values are also copied into both generated
gym manifests. No other fly-brain project supplies a circuit or behavior.

`make gym-build` reproduces `data/circuits/gym-v1-runtime.json` and
`data/circuits/gym-v1-learning.json`. The builder verifies the three full asset
checksums before selection. Gym startup validates every selected runtime,
food-learning and gym-learning edge against the official weights table, and
resolves labels and transmitter calls from the official annotations. The
reproduction test compares complete generated documents with tracked manifests.

The runtime preserves the existing DM1 food and L1/L2 vision routes. DM2 routes
start at officially annotated ORN_DM2 neurons and terminate at the same six
descending-neuron motor roles. Selection uses acetylcholine-only paths, edge
weight at least 10, and at most four hops. Ties prefer shortest paths, largest
bottleneck weight, largest weight product, then ascending body IDs. The manifest
records all selected paths. The resulting compact runtime contains 91 nodes and
92 structural edges. It is a selected circuit, not a complete brain.

The gym learning branch uses official DM2_lPN bodies L11092 and R12171, selected
from the official bilateral candidates. It excludes every KC used by the DM1
learning branch. For each candidate PN, PN-to-KC-to-MBON01 pairs rank by descending
minimum edge weight, descending product, then ascending KC ID. A candidate needs
24 paths. The chosen PN maximizes the minimum bottleneck over its best 24 paths,
then their summed products, then prefers the smaller PN ID. This yields 24
disjoint KCs per side and 48 plastic edges. Four strongest same-side ORN-to-PN
edges per side are recorded separately. All 104 gym learning edges are checked.

The existing official MBON01 endpoints are L520151 and R10013; the existing
official PAM01 set is retained. MBON01's official glutamate call is validated,
but no fast-current sign is assumed. PAM01 remains modulatory. The food and gym
branches keep separate eligibility traces and separate bounded multipliers even
though they share the same annotated MBON01 endpoint types. This separation is
an experimental learning model, not evidence of naturally independent pathways.

## Model assumptions, not biological findings

DM2 means the synthetic station odor in this experiment. MaleCNS does not label
a gym, exercise preference, pleasure, or a gym reward neuron. Structural paths
do not establish that the animal naturally seeks resistance walking. All arena
units, work units, fitness, fatigue, rate proxies and rewards below are
dimensionless model choices, not measured fly physiology or dopamine levels.

Each fly has one `ConnectomeNetwork`. DM1 and DM2 sensors are encoded together
before its network step. Each cue also has one `MushroomBodyLearning` state;
these are associative components of that brain, not alternative motor policies.
The existing sparse KC recall equation and learning defaults are retained:
eligibility decay 0.92, learning rate 0.08, active fraction 0.10, minimum edge
multiplier 0.35 and salience gain 1.0. The gym cue gain is
`1 + gym_association_strength`; food retains hunger gain multiplied by
`1 + food_association_strength`. Only the matching cue's encoding uses each
gain. Reward never directly produces movement. `--no-learning` disables updates
and learned gain while preserving loaded memory and ordinary sensory dynamics.

## Physical equations and initial conditions

The common arena remains 20 by 12. The resistance lane is centered at (0, 0),
width 16, height 8, resistance 2. Station odor at (x, y) is
`1 / (1 + (x^2 + y^2) / 9)`. Both antennae sample this field using the
existing 0.32 forward and 0.28 lateral offsets. Food and gym odors are separate
physical samples, and food vision retains the existing implementation.

For zero-based fly index `i`, initial position is
`(-6.4 + 3.2*(i % 5), -2 + 4*(i // 5))`, heading `0.22 + 0.12*i`,
and hunger 0.42. Starting on the lane is an explicit experimental exposure,
not learned station selection. This five-by-two physical grid separates initial
body centers by at least 3.2 units without observer offsets or steering.
All initial neural activities are zero.

At each step, the load is station resistance when the body begins inside the
lane, otherwise zero. Capacity is `(1 - 0.75*fatigue)*fitness` and applied forward
drive is `neural_forward * min(1, capacity) / (1 + load)`. The ordinary maximum
speed 3 and maximum turn rate 2.8 remain in `FlyBody`. The arena then constrains
the displacement. Work is `actual_displacement * load * inside_fraction`, where
the straight movement segment is clipped to the lane rectangle. A step entering
from outside earns no work because no load was applied until the next step;
an exiting step earns work only for its inside segment. This conservative,
discrete contact model is timestep-dependent. It is not a continuous contact
solver. Stationary turning and pushing against a wall cannot accumulate work.

Effort is `min(1, step_work / (3*dt))`. Fatigue is clamped to 0..1 after
`fatigue += dt * (0.18*effort - 0.06*(1-effort))`. Low effort therefore recovers
capacity without a world-level rest policy. Every 1.5 cumulative work units
completes a set; partial progress is `(total_work % 1.5) / 1.5`. Each newly
completed set produces one reward of 0.9; the gym learning branch is reinforced
once for each set, including when several finish in one coarse timestep. The
frame's reward is one bounded pulse indicating completion during that frame.
A following stationary step has zero reward. Fitness increases 0.005 per set,
capped at 1.5. Fitness affects loaded capacity as fatigue rises; it does not
raise the baseline maximum speed. Cumulative `distance` includes all actual
displacement and provides the browser's walking-animation phase.

Food contact uses the existing food radius, intake `0.30*dt`, metabolism 0.004
per second and digestion efficiency 0.8. Experiment 2's food reward is 0.3;
the gym pulse is therefore stronger. Extra hunger rises by
`0.002*effort*dt`. Hunger remains bounded. Experiment 1's reward and memory
identity are unchanged. The shared food spawner advances once per gym tick,
using fly-1's position for its existing minimum spawn-distance constraint.
Contact is processed in stable fly-ID order; the first consuming fly removes
the source. This introduces a deterministic tie bias. Flies do not collide
with one another. No world function chooses food, training, rest or a turn.

## Population, memory and observations

Stable identities fly-1 through fly-10 share immutable circuit declarations but
have independent mutable networks, physiology, eligibility, work and memory.
Only the first requested count are active. Removed identities remain in the
ten-slot bank and regain the same body and memories when restored. A count
change is applied at the next clock boundary even while paused; it does not
advance physics. Counts must be actual integers in 1..10, excluding booleans.

Persistence is performed by the application boundary under
`data/runs/experiment-002/fly-N/{food,gym}-memory.json`. Each channel has a
distinct Experiment 2 model identity plus dataset, official weights checksum
and exact plastic-edge identity. All ten slots are checked at startup so a
corrupt inactive fly cannot be silently reset. The existing repository writes
each file atomically. The two channel files are individually atomic, not a
multi-file transaction. Body state, workout statistics and fatigue are not
persisted across process restarts. Count reduction is non-destructive; there is
no gym memory reset command. Use separate directories for controlled comparisons.

Schema 2 carries a `gym_frame` with immutable per-fly snapshots; each nested
`frame` retains schema 1. Browser commands only pause/resume or change population.
Station geometry is carried in `hello`. The observer receives actual selected
runtime IDs, labels and activity. It does not receive all MaleCNS neurons, and
the geometric halo is not a reconstruction of this circuit.

## Initial finite comparison and limitations

A fresh three-fly, seed-7 comparison at 0.1 seconds per tick for 600 ticks,
using the current 16-by-8 lane and separated initial grid, completed 21, 6 and 4
sets with either learning enabled or disabled. Enabled gym association reached
approximately 0.04179, 0.01718 and 0.01060; disabled association remained zero.
Food association stayed zero. Enabled work was approximately 32.6281, 10.2278
and 7.1465 units; disabled work was 32.6424, 10.2588 and 7.1778. Peak fatigue
was 0.56281 enabled and 0.56107 disabled, with final fatigue recovered to zero.
Enabled learning did not improve set counts. These measurements supersede the
earlier smaller-lane, overlapping-start run. A fresh ten-fly 100-tick smoke
completed sets `[2,3,3,1,1,2,2,2,1,1]` in 0.3395 seconds of headless CPU time
after loading/composition. These outcomes demonstrate actual work-triggered plasticity, not a
validated exercise preference or guaranteed behavioral improvement. Multi-seed
learning efficacy, better motor calibration and continuous contact mechanics
remain unvalidated. Compact gym is supported; full gym is explicitly rejected.
