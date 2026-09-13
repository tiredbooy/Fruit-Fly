# 3D observatory: operation and maintenance

Run `make gym FLIES=3` and open <http://127.0.0.1:8000> for Experiment 2.
Set 1-10 in the count field and apply; select a fly to inspect its actual state.
`make web` preserves Experiment 1; `make web-full` selects its full MaleCNS graph.
The gym currently supports compact mode only.
Its schema-3 scene contains guided bench presses and paired dumbbells. The
selected-fly panel shows exercise, stroke phase, completed repetitions and
recovery; three full up/down repetitions complete one set. Equipment motion
and foreleg grips follow Python joint position, never render time. Apparatus
is authored Three.js geometry, with static parts merged by material, not a new
download or third-party dependency. The browser still reads legacy schema 2.
The default camera shows the arena; drag to orbit, scroll/pinch
to zoom, and select the fly-follow control for a close view. Keyboard users can
focus the canvas, use arrow keys to pan, and `+`/`-` to zoom. Camera controls do
not affect the simulation. All browser controls are labeled in Persian.

## Fly-eye view and neuron inspection

Choose **نمای چشم مگس** to observe from a head-height forward camera. Overview
and follow controls exit this mode and restore orbit/zoom. The view updates with
the body's position and heading, including when selected while paused; it never
sends movement commands. Only the selected fly's body is hidden to avoid
blocking the camera. This is an approximate view of the rendered arena, not a
compound-eye reconstruction or the brain's actual simple vision input.
While attached to equipment, the camera follows the authored head's actual
height and the received support orientation, including an inverted bench pose.
Exiting eye mode restores the world-up axis for ordinary navigation.
In eye mode the non-interactive canvas leaves the keyboard tab order and its
accessible description switches to the approximate viewpoint. Overview/follow
restore the canvas's keyboard controls and matching instructions.

The neuron panel leads with a rotatable 3D point cloud of measured somata from
our pinned MaleCNS annotations: 139,659 positions among 166,606 eligible bodies.
Dim points have no received reading; amber means received zero; pink means a
positive simulator rate. Missing coordinates are counted, never invented.
Drag to rotate or focus the map and use arrow keys and `+`/`-`. Hover a received
point for its official identity. Search filters received highlights, not the
background atlas. No lines imply unknown connections, and no pulses imply spikes.

Open the exact-readings disclosure for all records received in the latest frame.
Search official labels or numeric IDs. Rows are ordered by
measured activity, with IDs breaking ties. Zero values remain available for
inspection. Bars are display-clamped; numerical readings, including scientific
notation for tiny activity, remain visible. The positive/received count is not
the full brain's active population; the wire format permits at most 128 records.
Full mode retains its 70 configured interface bodies plus up to 58 strongest
positive non-interface readings within the same 128-record limit. It continues
updating the entire graph internally. Filtering is local and never queries or stimulates neurons.

Search stays focused as new frames arrive. Loading, no matching records, and
zero-activity states are distinct. Neuron inspection remains available when the
3D model or graphics backend fails.
The same DOM rows survive consecutive frames and reordered activity rankings;
only changed readings are updated. This does not reduce the received subset or
round away tiny values. The six descending-neuron rows are also retained.
See [observation assumptions](science/observation.md) for the camera geometry and
the distinction between rate-proxy telemetry and biological neural activity.

The graphics label displays **WebGPU** only when that backend initialized.
Otherwise Three.js uses **WebGL2**. Append `?renderer=webgl` to force fallback
when troubleshooting. Use localhost or HTTPS for WebGPU; an ordinary LAN HTTP
address is not a secure context. Do not require experimental browser flags for
normal use.

## Code map

| File | Responsibility |
| --- | --- |
| `main.ts` | Start telemetry immediately; asynchronously attach the scene and replay latest state |
| `graphics-renderer.ts` | Initialize graphics, configure rendering quality, identify backend |
| `fly-model.ts` | Load and orient the local authored skeletal GLB |
| `animated-fly.ts`, `fly-population.ts` | Independent rigs, distance-sampled walking, selected-fly rendering |
| `equipment-scene.ts`, `equipment-meshes.ts` | Shared authoritative weight/grip stroke and merged apparatus geometry |
| `foreleg-pose.ts` | Two-bone posing of the authored forelegs to actual weight handles |
| `equipment-snapshot.ts`, `gym-snapshot.ts` | Strict schema-3 equipment and legacy schema-2 parsing |
| `gym-scene.ts`, `gym-dashboard.ts` | Legacy lane scene, count/selection and measured exercise metrics |
| `neuron-map.ts`, `neuron-anatomy.ts` | Measured soma cloud and official-ID activity joins |
| `world-scene.ts` | Arena solids, surrounding support surface, and illumination |
| `scene-camera.ts` | Overview, orbit/zoom, follow, and approximate eye view |
| `fly-scene.ts` | Render supplied telemetry and release renderer resources |
| `scene-math.ts` | Coordinate/heading transforms, eye pose, and perspective fitting |
| `neuron-inspector.ts` | Searchable live neuron rows, counts, and honest empty states |
| `neuron-readings.ts` | Pure non-mutating neuron filtering and activity ordering |
| `assets/fly/` | Optimized GLB, provenance manifest, and attribution |

All paths above are under `frontend/web/src/`. The asset URL is hashed by Vite
and served through the existing `/assets/` route. Raw archives are git-ignored;
the small derived GLB is tracked. The browser makes no Sketchfab/Zenodo requests
during ordinary operation. Credits link to those sources only when selected.

## Current rig and measured anatomy

`walking-fly.glb` is the unchanged 307,672-byte authored rig from the user's
fly-escape project. `walking-source.json` records its commit, SHA-256, clips and
display transformations. The user authorized local visual reuse; the source
does not supply a public redistribution license. No brain/control code or
anatomical dataset is copied. Keep the legacy CT attribution separate.

Independent skeletons share geometry. Cumulative actual displacement samples
the Walk clip; ingestion samples Feed. Stationary flies do not walk merely
because time passes. Fly/Land clips are not used without Python flight state.
The stride and display scale are illustrative, not measured biomechanics.

Rebuild the public soma asset with:

```bash
.venv/bin/python -B scripts/export_neuron_positions.py
make frontend-test
```

The exporter checks the annotation checksum, applies the official valid-class
filter, omits absent/nonfinite coordinates, sorts IDs and uses one uniform
normalization. The JSON records source, license, counts and transformation.
The point cloud and fly scene have independent graphics lifecycles; a failure in
either leaves numeric telemetry usable. Activity geometry is updated on frames;
rendering skips hidden/offscreen maps. Positive overlays render above the dense
transparent atlas so low positive rates remain visible without changing values.
Teardown disposes point-cloud geometry/materials as well as mesh/line resources,
deduplicating shared resources across actors.

## Rebuilding the legacy CT asset

Create a separate environment; these are offline asset tools, not app runtime
dependencies:

```bash
python3 -m venv /tmp/flybrain-mesh-tools
/tmp/flybrain-mesh-tools/bin/pip install numpy==2.5.3 trimesh==5.1.0 fast-simplification==0.2.0
mkdir -p data/raw/visuals
curl -fL https://zenodo.org/api/records/14838021/files/Drosophila.zip/content -o data/raw/visuals/drosophila-14838021.zip
/tmp/flybrain-mesh-tools/bin/python scripts/build_fly_asset.py
make frontend-test
```

The converter validates the published archive checksum before processing only
the four named external surfaces. It records output SHA-256 and triangle counts
and retains a 59,500-triangle budget. Changing the source or conversion requires
reviewing the model visually and updating attribution and the manifest. Trimesh
may report that SciPy is unavailable and use its slower normal-calculation
fallback; this does not affect runtime requirements.

## Verification

`make frontend-test` verifies the shipped asset's hash, GLB structure, mesh
budget, camera fitting, eye-pose transforms, neuron filtering, and telemetry parser.
`make test` checks the Python loop,
protocol restrictions, and paused reconnection. `make frontend-build` includes
strict TypeScript checks and a production build.

For real-browser checks, install Playwright separately, start `make web`, and
run `scripts/check_observatory.py` using that environment's Python. Pass
`--browser /path/to/chromium` when necessary. The script checks the loaded model,
pause/resume, camera controls, responsive overflow, errors, and screenshots.
It also compares every inspector row's official ID, label, numeric activity, and
meter to an actual paused WebSocket frame; checks case-insensitive label/ID
search and focus retention; and verifies no observer action sends a command.
Camera controls are checked at 320px as well as the captured 390px mobile layout.
`--webgpu` requires a working native WebGPU adapter and fails if the browser falls
back; it does not bypass driver blocklists or change system settings. Without
that flag it checks the explicit WebGL2 fallback with software GL. Screenshots
go to ignored `.impeccable/review/`. Checks also cover paused reload and failed
asset loading with live instruments preserved.

For the gym, start `make gym` and run `scripts/check_gym_browser.py --url
http://127.0.0.1:8000` with that separate Python environment. It checks 1-10-1
population changes while paused, selected-fly exact readings, visible anatomical
activity pixels, camera-only controls, paused reload, 320/390px layouts and
independent missing-model/missing-anatomy behavior. No test substitutes a fake
simulation or fabricated neural frame.

For articulated motion, run `scripts/check_equipment_browser.py --url
http://127.0.0.1:8000` against a freshly started three-fly gym. It pauses before
graphics loading, observes real bench/curl strokes, checks complete reps/sets,
captures overview/follow/mobile, and checks that observer actions send no motor
commands. `scripts/check_neuron_updates.py --url http://127.0.0.1:8000` verifies
that all received neuron rows, role rows and search focus survive live updates.
These checks require the separate Playwright environment described above.
Three.js pose transformations follow the [Object3D API](https://threejs.org/docs/pages/Object3D.html)
and [quaternion rotations](https://threejs.org/docs/pages/Quaternion.html); the
joint equations and pose assumptions are ours, documented in
[equipment science](science/equipment.md).

The browser regression also triggers actual WebGL context loss during a delayed
GLB request and after scene readiness. Both must leave instruments running and
the graphics error visible. Renderer callbacks preserve Three.js's own lost-device
guard, stop the animation loop, and latch failure across asynchronous startup;
later model completion must never overwrite that failure with a ready label.
Closing observers during a broadcast must also leave Python's clock running;
the server removes failed connections individually. A real-connection regression
forces the send/close race, while separate tests ensure cancellation and invalid
serialization still propagate rather than being hidden as transport errors.

This development environment exposes no `/dev/dri` GPU devices. A minimal WebGPU
clear-pass probe, independent of Three.js, failed to create a device with the
SwiftShader ANGLE configuration (`A valid external Instance reference no longer
exists`); Vulkan configurations returned no adapter. WebGL2 is verified here;
native WebGPU and hardware frame-rate gains still need a supported device.

The shared lazy Three.js bundle is approximately 845 KB before compression
(229 KB gzip), plus the 308 KB rig and separately fetched measured soma JSON.
Vite reports its existing 600 KB chunk
warning. Instruments load independently; no additional JavaScript dependency or
remote asset request was introduced.

The legacy CT scan has no rig; the current authored rig animates actual walking
and feeding. Ground-walking physics and the sensory world remain two-dimensional.
The 3D presentation does not add flight, fear, obstacles, or hidden steering.
