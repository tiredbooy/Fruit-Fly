# Decision 0004: WebGPU and a licensed CT fly surface

Date: 2026-09-13
Status: Accepted by the user's model-substitution and WebGPU requests

## Context

The initial Three.js view used primitive body geometry, an orthographic camera,
and WebGL. The requested Sketchfab model did not offer a download or declared
license, and the user authorized another internet model.

## Decision

Use the CC BY 4.0 external CT surfaces from Zenodo 14838021. Keep source identity,
author credit, license, specimen sex, transformations, and checksums next to the
optimized 1.43 MB GLB. No renderer-time external download or login is needed.

Use the installed Three.js `WebGPURenderer`, initialized asynchronously, with
its WebGL2 backend fallback. Alias addon imports to the same `three/webgpu`
core to prevent duplicate engine classes. Keep the small instrument client
independent of the lazy-loaded graphics bundle. Display the actual backend.

Use a perspective camera, Three.js OrbitControls, a solid arena with visible
depth and shadowed lighting, and observer-only overview/follow controls.
The geometry depicts the existing bounded ground plane. Flight, climbing, and
collision-aware obstacles require future Python physics and sensory work;
decorative geometry must not silently become an unmodeled physical obstacle.

## Why these pieces fit

Python still supplies x/y/heading, food, and neural telemetry; the browser maps
them to the X/Z ground plane. OrbitControls moves the camera only. Reloaded
observers receive the current running state and cached frame even while paused.
Asynchronous graphics startup buffers the latest frame without delaying live
instruments. Model or device failure leaves the measurements visible.

## Costs and limits

The asset is a female scan, used only for appearance in a MaleCNS simulation.
It has a fixed pose and illustrative colors. It is not a rigged biomechanical
body or measured correspondence between body surface and individual neurons.

WebGPU requires browser/adapter support and a secure context (localhost or
HTTPS). It accelerates rendering, not the Python/SciPy brain. Performance must
be measured on the user's device; merely selecting WebGPU does not guarantee a
frame-rate improvement. The larger graphics bundle loads separately.
