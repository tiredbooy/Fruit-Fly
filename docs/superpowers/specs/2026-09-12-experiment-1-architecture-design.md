# Experiment 1 Architecture Design

## Goal

Build the first experiment of an original fruit-fly simulation engine using the
official MaleCNS connectome. One simulated fly must interact with one food
source through smell, simple vision, hunger, neural activity, and body movement.
The world must never choose behavior for the fly.

## Scope

Experiment 1 includes:

- One two-dimensional arena.
- One fly with position, heading, body motion, and hunger.
- One food source with odor, visual appearance, and nutrition.
- Bilateral smell and simple retinotopic grayscale vision.
- A MaleCNS-backed neural simulation and data-backed motor readout.
- A live Persian terminal monitor and replayable telemetry.

Predators, competitors, fear, reproduction, multiple flies, learning, and the
Three.js frontend are outside Experiment 1. The architecture must allow these
to be added without moving behavioral decisions into the world.

## Architectural Style

Use a modular monolith with explicit boundaries. `brain` and `world` do not
import each other. The application-level simulation loop coordinates them using
small immutable signal objects. `main.py` is a composition root and contains no
simulation or behavioral policy.

```text
brain/
├── data.py
├── circuit.py
├── neuron.py
├── network.py
├── sensory.py
├── modulation.py
└── readout.py

world/
├── environment.py
├── food.py
├── fly.py
├── sensors.py
└── motor.py

simulation/
├── signals.py
├── telemetry.py
└── loop.py

frontend/
└── console.py

experiments/
└── experiment_001.toml

data/
├── malecns/v1.0/source-manifest.json
├── circuits/foraging-v1.json
└── runs/

tests/
main.py
```

## Dependency Boundaries

### World

The world owns physical facts only: arena geometry, fly pose, food location,
odor concentration, light or contrast, contact, and food quantity. It does not
know neuron IDs, neural activity, hunger-driven goals, or desired movement.

### Brain

The brain owns the selected MaleCNS graph, neuron state, neural dynamics,
sensory encoding, hunger modulation, and motor readout. It receives physical
measurements rather than `Food` or `Environment` objects.

### Simulation

The simulation loop owns time and flow of control. It converts no world fact
directly into behavior; it only transports typed values between boundaries.

### Presentation

The console observes immutable telemetry frames. It has no reference that lets
it mutate the fly, world, neural state, or simulation clock.

## Continuous Simulation Loop

Each fixed simulation tick performs these operations in order:

1. Sample odor and visual fields at the fly's antenna and eye positions.
2. Encode those physical samples as stimulation of verified MaleCNS neurons.
3. Apply continuous hunger modulation and advance the neural network.
4. Decode verified neural output populations into abstract motor drive.
5. Integrate body movement, food contact, ingestion, and metabolic state.

No branch may directly translate a world condition into a motor command. In
particular, code equivalent to `food_is_left -> turn_left` is forbidden.

## MaleCNS Data Contract

The canonical source is the official MaleCNS `v1.0` release. Runtime simulation
uses a locally materialized, validated circuit rather than depending on a live
neuPrint connection.

The source manifest records:

- Dataset name and exact version.
- Dataset UUID when available.
- Official source URLs and license.
- SHA-256 hashes of downloaded files.
- Import timestamp and importer version.

The circuit manifest records each selected neuron's `bodyId`, official `type`,
`instance`, side, role, selection query, functional evidence, confidence, and
modeling assumptions. Selection is resolved from official data queries rather
than IDs copied from memory.

The importer rejects missing IDs, duplicate IDs, mismatched annotations,
unresolved bilateral requirements, and silently inferred transmitter polarity.
Unknown biological properties remain explicitly unknown until supported by
evidence or approved as a modeling assumption.

Official sources:

- https://male-cns.janelia.org/download/
- https://neuprint.janelia.org/ (`male-cns:v1.0`)
- https://reiserlab.github.io/celltype-explorer-drosophila-male-cns/

## Sensory Boundaries

### Smell

The environment computes odor concentration in space. Two antenna sample
concentration independently. The brain adapter converts those concentrations
to activation of an officially annotated bilateral olfactory population.

Experiment 1 uses an apple-cider-vinegar-like food odor and the `ORN_DM1`
pathway as the first hunger-modulated candidate. Published evidence identifies
Or42b/DM1 as necessary for starvation-enhanced food search and reports enhanced
DM1, DM2, and DM4 responses to apple cider vinegar:

https://pmc.ncbi.nlm.nih.gov/articles/PMC3073827/

### Vision

The environment exposes grayscale light or contrast by direction, not object
identity. A coarse retinal sampler projects the visible food shape into angular
sectors. MaleCNS `v1.0` annotates photoreceptor types such as `R1-R6`, but its
retinal hex-coordinate fields are populated on downstream retinotopic optic-lobe
types such as `L1` and `L2`, not on the `R1-R6` rows. Experiment 1 therefore
injects grayscale signals into officially annotated `L1`/`L2` neurons selected
with `assignedOlHex1`/`assignedOlHex2` coordinates.

The initial retinal resolution and omission of explicit `R1-R6`
phototransduction are modeling assumptions. They must not be presented as
properties supplied by MaleCNS.

## Hunger and Ingestion

Hunger is a bounded physiological state owned by the fly:

- `0.0` represents full.
- `1.0` represents starving.
- Metabolic expenditure increases hunger continuously.
- Consumed nutrition decreases hunger continuously.

Hunger never activates a seek-food mode. It supplies a continuous modulator to
the brain. For Experiment 1, the modulator changes outgoing transmission from
the supported food-odor ORN pathway rather than changing the physical odor
field or multiplying every olfactory neuron.

Automatic ingestion on body-food contact is an explicit Experiment 1
simplification. It is body physiology, not navigation policy. A future feeding
motor circuit can replace this adapter without changing the world or brain
boundaries.

## Neural Dynamics

Use an original deterministic sparse rate-network engine implemented with
general-purpose NumPy and SciPy operations. Do not copy another fly-brain
project and do not introduce a neural-simulator framework for Experiment 1.

MaleCNS supplies neuron identities, synaptic structure, connection counts, and
predicted neurotransmitter information. It does not supply a complete runnable
dynamical model. These properties are explicit modeling assumptions:

- Neuron activation equation and decay.
- Simulation timestep and initial activity.
- Conversion and normalization of synapse counts.
- Handling of uncertain transmitter sign.
- Noise model, if noise is later enabled.

Every assumption must be documented in configuration or the circuit manifest.
No unknown polarity is silently converted to excitatory or inhibitory.

## Motor Boundary

The brain readout consumes only neural activity and produces an abstract motor
drive containing forward and angular components. Body physics consumes that
drive without inspecting sensors, food, or hunger.

Verified steering candidates in MaleCNS `v1.0` are:

| Type | Left body ID | Right body ID | Intended evidence-backed use |
|---|---:|---:|---|
| DNp09 | 10783 | 11177 | Forward-walking initiation; asymmetry can contribute to ipsilateral turning |
| DNa01 | 10442 | 10760 | Lower-gain steering component |
| DNa02 | 523769 | 10360 | Higher-gain steering component |

The bilateral DNa02 activity difference has experimental support as a predictor
of turning velocity:

https://elifesciences.org/articles/102230

DNp09 is an evidence-backed forward-walking candidate. Bilateral activation has
been reported to drive straight walking, while unilateral activation produces
forward walking with an ipsilateral turning component:

https://pmc.ncbi.nlm.nih.gov/articles/PMC9435592/

Experiment 1 uses bilateral DNp09 activity as its forward-drive readout and
bilateral DNa01/DNa02 differences as steering readouts. The exact conversion
from neural activity to physical speed remains an explicit calibration
assumption even when the neural populations are evidence-backed.

## Telemetry and Live Console

The simulation publishes immutable telemetry at a lower rate than the neural
and physics timestep. Each frame includes experiment ID, fly ID, simulation
time, body pose, hunger, bilateral sensor values, selected neuron activities,
and decoded motor drive.

The console displays real values and causal relationships. It does not invent
thoughts or intentions. Visible labels are Persian, including:

- `گرسنگی`
- `بوی چپ` and `بوی راست`
- `فعال‌ترین نورون‌ها`
- `خروجی حرکتی`
- `چرخش`

Selected activity is shown with official neuron type, body ID, side, and current
activation. A rate-limited console refresh prevents presentation from slowing
the simulation. Non-interactive execution falls back to line-oriented output.

Telemetry may also be written as JSON Lines under `data/runs/`. The future
Three.js frontend consumes the same telemetry schema through a separate
transport adapter; it must not require changes to brain or world modules.

## Scaling Strategy

The immutable connectome graph can be shared by future flies. Each fly owns its
own neuron activation, physiology, pose, sensor frame, and telemetry identity.
Future predators and competitors become world entities with physical signals;
fear and reproduction require new evidence-backed sensory, internal-state, and
motor circuits rather than world-authored behavior rules.

No multi-agent engine, entity-component system, predator model, or reproduction
model is implemented during Experiment 1.

## Testing Strategy

Tests must cover observable boundaries and causality:

1. Data-contract tests validate every selected ID and annotation against the
   pinned source data.
2. Dependency tests prevent `brain` and `world` from importing one another.
3. Sensor tests verify mirrored geometry produces mirrored physical samples.
4. Modulation tests verify hunger changes olfactory transmission continuously,
   without a behavioral threshold.
5. Deterministic integration tests verify that motor output comes through the
   neural path and that identical seeds produce identical trajectories.

Lesion experiments disable selected sensory populations to confirm that an
observed odor-guided bias depends on the modeled neural pathway.

## Experiment 1 Success Criteria

- One fly and one food source run in a deterministic continuous loop.
- Sensor values vary only from physical world state and sensor geometry.
- Hunger increases with metabolism and decreases when food is consumed.
- Hunger continuously modulates the evidence-backed food-odor pathway.
- Movement is decoded from MaleCNS network output without world behavior rules.
- The Persian console exposes the causal neural trace and can record a replay.
- All neuron roles and IDs pass provenance validation.

## Risks and Limitations

The connectome alone does not guarantee that an assumed dynamical model will
produce biologically realistic food seeking. A successful trajectory is an
experiment result, not an architectural assumption. Weight normalization,
unknown transmitter effects, motor calibration, odor physics, retinal
resolution, and ingestion-on-contact must remain visible modeling choices.

Experiment 1 should favor deterministic, inspectable behavior over apparent
biological complexity. More detailed dynamics are justified only by evidence or
by a measured failure of the initial model.
