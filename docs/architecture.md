# Architecture

## Purpose

FlyBrain Lab is a modular, inspectable neural-control simulation. Experiment 1
uses one fly, one dynamic food source, hunger, smell, simple vision, a compact MaleCNS
sensor-to-motor subgraph, and persistent appetitive odor learning.

The architecture prevents environment code from deciding behavior. Every turn
and forward movement must pass through sensors, neural computation, and motor
readout.

## Package responsibilities

| Package | Responsibility | May depend on |
| --- | --- | --- |
| `world` | Geometry, odor physics, randomized food lifecycle, food contact, body movement, physiology | `simulation.signals` |
| `brain` | MaleCNS data, circuit validation, neural dynamics, modulation, learning, memory state | `simulation.signals` |
| `simulation` | Immutable boundary signals and tick orchestration | `brain`, `world` |
| `experiments` | Concrete Experiment 1 composition and parameters | `brain`, `simulation`, `world` |
| `frontend` | Read-only terminal rendering of telemetry | `simulation.signals` |
| `main.py` | CLI, official asset loading, memory persistence lifecycle | all composition adapters |

The dependency rule is explicit: **world must not import brain**, and brain must
not import world. Data crosses those boundaries through immutable dataclasses in
`simulation/signals.py`.

## Continuous control loop

```text
+---------+     +---------+     +-------------+     +----------+
|  WORLD  | --> | SENSORS | --> | BRAIN       | --> | MOTOR    |
| food    |     | smell L |     | hunger gain |     | forward  |
| fly     |     | smell R |     | memory gain |     | turn     |
| fields  |     | vision  |     | MaleCNS net |     +----+-----+
+----+----+     +---------+     +-------------+          |
     ^                                                     |
     +-------------------- FLY BODY <----------------------+
```

No component can shortcut this loop with rules such as `food left -> turn left`
or `hunger high -> seek food`.

## Learning loop

```text
DM1 odor -> DM1_lPN -> sparse Kenyon cells -> MBON01 response
                              |
                              +-> eligibility trace
                                        |
food contact -> ingestion -> PAM01 reward
                                        |
                                        v
                              KC-to-MBON01 plasticity
                                        |
                                        v
                           learned odor-salience gain
```

Food contact creates a normalized reward signal after body physics. It never
creates a motor command. `BrainAdapter` applies the learned salience gain to the
next odor encoding, and the existing MaleCNS-derived network still produces the
motor output.

## Tick ordering

`Simulation.step(dt)` performs these operations in order:

1. `Environment` advances the random food lifecycle and may expose no food.
2. `SensorRig` samples physical smell and vision.
3. `BrainAdapter` recalls the odor representation and updates KC eligibility.
4. Hunger and learned salience continuously scale bilateral odor input.
5. `ConnectomeNetwork` advances five neural substeps.
6. `MotorReadout` converts named descending-neuron activity to forward/turn
   drive.
7. `FlyBody` moves and `Environment` constrains its position.
8. Physical food contact changes hunger, creates one reward, and removes the food.
9. The brain applies PAM-gated plasticity and returns immutable telemetry.
10. The application boundary atomically persists changed memory.

The food lifecycle is physical world state. It uses a local random generator,
waits between spawns, expires uneaten food, usually places food far inside the
arena, and sometimes places it outside the fly's accessible bounds. Missing food
produces zero smell and vision rather than a behavioral instruction.

This order ensures that reward modifies the odor representation that preceded
the rewarded contact.

## Runtime circuits

`data/circuits/foraging-v1-runtime.json` contains the compact sensor-to-motor
subgraph. `data/circuits/foraging-v1-learning.json` contains the mushroom-body
learning subgraph. Both declare the SHA-256 of the official weights asset.

`make data-status` validates:

- dataset and asset checksums;
- role IDs, types, classes, sides, and transmitter calls;
- every compact edge triple against the 151,856,684-row official weights file;
- supported fast-current polarity and dopamine-only modulation.

## Memory ownership

`MushroomBodyLearning` owns in-process eligibility and immutable `MemoryState`.
It performs no file I/O. `MemoryRepository` is a JSON gateway used by `main.py`.
The default file is `data/runs/experiment-001-memory.json`.

The persisted schema binds memory to:

- schema version `1`;
- dataset `male-cns:v1.0`;
- official weights checksum;
- model `pam01-kc-mbon01-v1`;
- exact KC-to-MBON01 edge IDs and baseline weights.

Writes use a temporary sibling file, `fsync`, and atomic replacement. A reset
moves existing state to `.bak` before starting clean.

## Failure behavior

- Missing or corrupt official assets stop before simulation.
- An invented or mismatched learning role or edge stops validation.
- An incompatible memory schema, dataset, model, checksum, or edge set is
  rejected instead of silently reset.
- A failed save exits with an English ASCII error.
- `Ctrl+C` restores the terminal and saves the current memory.

## Extension points

Future experiments can add other odor channels, aversive PPL1 reinforcement,
visual associations, extinction, and memory consolidation by adding explicit
circuit manifests and learning models. They must not add environment-to-action
shortcuts or reuse DM1 association values as a universal memory system.
