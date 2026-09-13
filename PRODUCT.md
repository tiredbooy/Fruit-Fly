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
one fly, its environment, internal hunger, sensory input, neural activity,
learning, and motor output while every behavioral action remains produced by
the simulation rather than frontend or game rules.

## Positioning

The product exposes the continuous world-to-sensor-to-MaleCNS-to-motor loop and
keeps official biological identity separate from explicit mathematical model
assumptions. It does not copy another fly-brain project or describe numerical
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
- Compact and full-connectome neural engines share one brain boundary.
- Biological neuron IDs, annotations, transmitter calls, and structural edges
  come from checksum-pinned official MaleCNS data.
- World code and brain code cannot import each other or bypass the neural loop.
- The browser may pause/resume the clock but cannot steer the fly or inject
  simulation values.
- The approved roadmap is fly gym, general learning, Three.js observation, then
  evaluation of poker as a later research task.

## Brand Commitments

The confirmed name is FlyBrain Lab. Browser UI is Persian/RTL; terminal text is
English. Official neuron labels and IDs remain unchanged. The user wants to see
what is happening rather than read narrative descriptions.

## Evidence on Hand

- Pinned MaleCNS source manifest: `data/malecns/v1.0/source-manifest.json`
- Scientific assumptions: `docs/science/`
- Verified runtime and benchmark state: `docs/status.md`
- Existing terminal observer: `frontend/console.py`
- There are no supplied brand assets, anatomical meshes, or licensed fly models;
  the browser must not fabricate them as evidence.

## Product Principles

1. Show measured state instead of narrating thoughts.
2. Keep behavior inside the embodied neural loop.
3. Preserve scientific provenance and label every model assumption.
4. Make experiments observable, repeatable, and locally runnable.
5. Add complexity only when the preceding milestone can measure it.

## Accessibility & Inclusion

The browser must remain keyboard operable, preserve visible focus, support
reduced motion, provide semantic live states, and adapt from desktop to narrow
mobile layouts. The data panel remains usable when WebGL is unavailable.
