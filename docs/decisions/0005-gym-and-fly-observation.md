# Decision 0005: Gym, population, and fly observation

Date: 2026-09-13
Status: User-approved design, including fly-eye view and active-neuron inspection

## Approved direction

Experiment 2 combines resistance walking with food-seeking. Python remains the
only simulation authority. One to ten flies share a world and immutable source
data, but never mutable neural activity, fatigue, hunger, or learned memory.
The browser's count field applies a validated population change at a tick
boundary. Existing flies retain memory; removed flies' memory is preserved.
Experiment 1 and its existing memory file remain unchanged.

A resistance lane measures completed work from physical movement under load.
Only a newly completed set produces a bounded experimental reward pulse. It is
not a measured dopamine concentration, a promise of pleasure, or a motor command.
Food and gym cue learning must be distinguishable and backed by official MaleCNS
identities and structural edges. Any physiological gain, task cue, learning
equation, or reward schedule is an explicitly documented model assumption.
No world rule chooses between eating, training, and rest. Training curves show
observed outcomes, including failures, and are compared with learning disabled.
Compact mode is the initial validation target; full mode needs calibration and
performance measurement before promising a ten-fly real-time workload.

## Fly-eye view

The observer has overview, follow, and eye camera modes. Eye mode follows the
selected body's position and heading, uses a head-height forward camera, and
hides that body's mesh so it does not obstruct the view.
Eye mode does not accept steering input. Leaving it restores orbit/zoom and the
body. Its label states that it is an approximate camera view, not a compound-eye
reconstruction or the actual four scalar sensor inputs used by the brain.

## Neuron inspector

The selected fly's received neuron records supply official IDs, labels, and
measured rate-proxy activity. The inspector makes activity visible with bounded
bars and supports ID/label filtering. It must distinguish the received subset
from a whole-brain active count, retain exact numerical values, and present zero
activity honestly. No invented neuron, connection, anatomical position, or
spiking animation is added. Existing named descending-neuron outputs remain
visible. Selection and camera changes never alter simulation state.

## Delivery boundaries

The observer additions are an independently testable first slice. Neural cue
provenance, multi-fly physics/reward/persistence, and the gym's versioned wire
protocol follow as separate integration slices. Their approval is recorded here;
normal implementation steps do not require repeated approval. Each slice must
update architecture, status, scientific assumptions, and verification evidence.

Observer slice delivered on 2026-09-13: approximate eye camera and searchable
received-neuron inspector, using the unchanged single-fly schema. Verified on
actual compact and full backends; this delivery does not implement workouts or
population control. The implementation remains reusable for a selected-fly frame.

Internet assets may provide licensed appearance only, with source, credit,
license, checksum, and transformations tracked. The existing female CT fly has
no leg rig; it is not sufficient evidence for human-style weightlifting or
anatomically faithful exercise. New biomechanics are separate from camera work.

## Completed gym integration and visual clarification

The subsequent user request explicitly authorized useful visual reuse from
their local fly-escape project and clarified that neuron inspection must include
a spatial UI. The integrated delivery now supplies actual resistance walking,
1-10 independent compact brains, distinct food/gym memory, schema-2 population
control, selected-fly instruments and a measured anatomical point cloud.
Positions are exported from our own pinned MaleCNS annotations; no reference
brain code, controller, IDs, graph edges or anatomical data are imported.

The reference project's authored rig supplies walking and feeding clips. Its
unchanged checksum, source commit and licensing uncertainty are recorded.
Reuse authorization is not a public redistribution license. Movement samples
walking; ingestion samples feeding. Unused flight clips do not imply airborne
physics, which remains outside this implementation.

Initial conditions are a 20-by-12 world with a 16-by-8 central resistance lane.
Up to ten flies start on a separated 5-by-2 physical grid inside that lane;
this is deliberate experimental exposure, not learned station seeking.
There are no browser-only offsets or inter-fly collision mechanics.
The finite learning-on/off baseline changes association but has equal set counts;
it does not establish exercise preference, addiction or subjective reward.
See [current status](../status.md) and [gym model](../science/gym.md).
