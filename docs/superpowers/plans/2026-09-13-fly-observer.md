# Fly-eye and neuron observer implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox syntax for tracking.

**Goal:** Add a body-relative eye camera and a readable real-neuron activity inspector as the first observer slice of approved Experiment 2.

**Architecture:** Reuse the existing Three.js scene, observer-only camera, and schema-v1 frame. Extract neuron presentation from Dashboard into a focused inspector that consumes one fly's frame, so a subsequent population adapter can supply the selected fly without redesigning this component.

**Tech Stack:** Existing TypeScript, Three.js, Bun, Vite, Python/aiohttp. No new runtime dependency.

**Spec:** `docs/decisions/0005-gym-and-fly-observation.md`

## Global Constraints

- Browser copy is Persian/RTL; terminal text and documentation are English.
- Every displayed neuron ID, label, and activity comes from received telemetry.
- Camera and inspector actions cannot change simulation state or send steering.
- The eye camera is an approximate visual viewpoint, not compound-eye biology.
- Preserve existing WebGPU/WebGL2 initialization, failure handling, and mobile behavior.
- Do not rewrite or discard the existing uncommitted 3D upgrade.
- This task does not change the Python brain, world, wire schema, or memory.

### Task 1: Eye camera and real-neuron inspection

**Files:**
- Modify `frontend/web/src/scene-camera.ts`, `scene-math.ts`, `fly-scene.ts`, `main.ts`, `dashboard.ts`, `scene-controls.css`, `frontend/web/index.html`.
- Create `frontend/web/src/neuron-inspector.ts`, `neuron-readings.ts`, `neuron-inspector.css`, `neuron-readings.test.ts`.
- Extend `frontend/web/src/fly-scene.test.ts`.
- The coordinator updates project documentation and browser checks after implementation.

**Interfaces:**
- Consume `FrameMessage` and `ActiveNeuron` from existing `types.ts` without protocol edits.
- Expose `SceneCamera.eyeView(position: Vector3, heading: number): void`, `SceneCamera.mode: "overview" | "follow" | "eye"`, and `SceneCamera.update(position: Vector3, heading: number): void`.
- Expose `FlyScene.showEyeView(): void`; update all camera modes' pressed state and announce the active mode in Persian.
- Expose `NeuronInspector.update(frame: FrameMessage): void`; Dashboard delegates its existing neuron list update to it.
- Pure `eyeCameraPose(x: number, z: number, heading: number)` returns `{position: {x,y,z}, target:{x,y,z}}`: head offset 0.8, height 0.65, forward look distance 6, level view. Display units are explicitly approximate.
- Pure `filterNeuronReadings(neurons: readonly ActiveNeuron[], query: string)` returns a sorted copied array; search ID and case-insensitive label, descending activity then ascending ID. All received records are searchable, including zero values. Do not mutate the input.

- [x] Write failing camera math and filtering tests before implementation:

```typescript
expect(eyeCameraPose(2, 3, 0)).toEqual({position:{x:2.8,y:0.65,z:3},target:{x:8.8,y:0.65,z:3}});
const readings = [{body_id:63316,label:"L2",activity:0.2},{body_id:10783,label:"DNp09",activity:0}];
expect(filterNeuronReadings(readings, "dnp").map(n => n.body_id)).toEqual([10783]);
expect(filterNeuronReadings(readings, "63316").map(n => n.body_id)).toEqual([63316]);
```

- [x] Run `cd frontend/web && bun test`; record the missing-feature failures.
- [x] Implement the camera and inspector contracts. In eye mode disable OrbitControls and keyboard zoom, set FOV 90 and near plane 0.03, follow heading with the same x/cos and z/-sin convention as world-to-scene. Overview/follow restore FOV 45 and near 0.1. Hide only the observed body's mesh and halo while in eye view and restore them on exit; do not lose the has-frame guard. Add a third camera button, an honest eye-view caption, a bound search field, and measured activity bars. Keep the visible panel bounded/scrollable, preserve focus during live updates, and show received-subset counts rather than a fabricated total. Empty/no-match/loading remain distinct. Reuse existing native buttons and meter/progress styling rather than installing React controls.
- [x] Run `cd frontend/web && bun test && bun run build`; report exact results and any existing size warning.
- [x] Self-review input immutability, mode changes, negative coordinates/headings, inactive records, safe text rendering, disabled/loading states, and preservation of Python authority.
- [x] Record the implementation and RED/GREEN evidence in the task report. Leave changes uncommitted for a coordinated review of this checkout; no push, reset, or checkout of existing files.

## Coordinator verification and subsequent integration

- [x] Run the actual compact simulation in a browser: enter eye mode, verify body-relative orientation and no own-body obstruction, return to overview, search a received neuron ID, verify pause/resume and responsive layout. Exercise model-load failure and lost-context recovery messages.
- [x] Record a read-only task review, resolve material findings, then update `docs/frontend-observatory.md`, `docs/status.md`, `AGENTS.md`, and observer design records.

Subsequent, separately integrated work: gym implementation must use validated cue
circuitry and preserve the single-frame camera/inspector contract for a selected-fly
adapter. The observer delivery does not claim that workouts or population support
are already implemented.
