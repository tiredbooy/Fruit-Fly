# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python simulation with an aiohttp observer server and a framework-free
TypeScript/Three.js browser client built by Vite and Bun. The user explicitly
requested Three.js and approved this recommended stack.

## Users

The primary user is the project author or a technical observer studying how an
embodied fly simulation turns physical stimuli into MaleCNS-derived neural and
motor activity. They need to see state change directly instead of reading logs.

## Product Purpose

FlyBrain Lab is a from-scratch, inspectable fruit-fly neural-control simulation
built from the official MaleCNS connectome. Success means a person can observe
one to ten flies, their environment, internal hunger, sensory input, neural activity,
learning, and motor output while every behavioral action remains produced by
the simulation rather than frontend or game rules.

## Positioning

The product exposes the continuous world-to-sensor-to-MaleCNS-to-motor loop and
keeps official biological identity separate from explicit mathematical model
assumptions. It does not copy another project's brain or controller or describe numerical
telemetry as consciousness.

## Operating Context

The project runs locally from GNU Make commands. Python owns simulation and
persistent memory; the browser observes live telemetry over a local same-origin
WebSocket. Compact mode is useful for visible Experiment 1 movement. Full mode
updates 166,606 valid MaleCNS v1.0 bodies but currently produces motor activity
near `10^-6` because its gain has not been scientifically calibrated.

## Capabilities and Constraints

- One fly, a dynamic food source, hunger, bilateral smell, simple vision,
  locomotion, and appetitive olfactory memory are implemented.
- Experiment 2 adds 1-10 independently simulated compact brains, physical
  loaded bench presses and dumbbell curls, effort/fatigue, full-repetition set
  rewards, station-bound continuous training and separate food/gym memory.
- Compact and full-connectome neural engines share one brain boundary.
- Biological neuron IDs, annotations, transmitter calls, and structural edges
  come from checksum-pinned official MaleCNS data.
- World code and brain code cannot import each other or bypass the neural loop.
- The browser may pause/resume and configure gym population (1-10), but cannot
  steer, feed, select a workout action or inject neural values.
- The 3D arena uses perspective orbit/follow controls and a locally served,
  authored skeletal fly, with walking sampled from displacement and feeding from
  ingestion. WebGPU is preferred with WebGL2 fallback; physics remain grounded.
- A selected-fly eye camera and measured MaleCNS soma cloud expose received neural
  activity without inventing spikes, coordinates or subjective experience.
- Gym learning changes cue association; improved set counts, addiction and
  autonomous exercise preference are not established. Full-gym calibration,
  airborne flight and poker remain future work.
- Equipment poses and foreleg force are explicit task-model assumptions, not
  measured insect biomechanics. The observer follows actual joint telemetry.

## Brand Commitments

The confirmed name is FlyBrain Lab. Browser UI is Persian/RTL; terminal text is
English. Official neuron labels and IDs remain unchanged. The user wants to see
what is happening rather than read narrative descriptions.

## Evidence on Hand

- Pinned MaleCNS source manifest: `data/malecns/v1.0/source-manifest.json`
- Scientific assumptions: `docs/science/`
- Verified runtime and benchmark state: `docs/status.md`
- Existing terminal observer: `frontend/console.py`
- Licensed external body surfaces: Zenodo record 14838021, CC BY 4.0. Source,
  checksum, author credit, and transformations are in `frontend/web/src/assets/fly/`.
  This legacy female scan is not the MaleCNS specimen and remains attributed.
- Current rig: user-authorized visual reuse from their fly-escape project,
  tracked in `walking-source.json`; no public redistribution license supplied.
  No brain/control code or anatomical data is reused from that project.
- Measured anatomical export: 139,659 valid somata from our pinned annotations;
  absent coordinates and unreceived activity are explicitly distinguished.

## Product Principles

1. Show measured state instead of narrating thoughts.
2. Keep behavior inside the embodied neural loop.
3. Preserve scientific provenance and label every model assumption.
4. Make experiments observable, repeatable, and locally runnable.
5. Add complexity only when the preceding milestone can measure it.

## Accessibility & Inclusion

The browser must remain keyboard operable, preserve visible focus, support
reduced motion, provide semantic live states, and adapt from desktop to narrow
mobile layouts. The data panel remains usable when graphics or model loading
is unavailable.
