---
name: FlyBrain Observatory
description: A living specimen chamber with a restrained scientific instrument rail.
colors:
  chamber-black: "#070b0f"
  optical-slate: "#14202a"
  optical-line: "#29404d"
  arena-surface: "#53665b"
  specimen-cyan: "#58d6d0"
  food-amber: "#f2b84b"
  motor-magenta: "#e36da6"
  paper-white: "#e8efef"
  muted-cyan: "#8aa6aa"
  danger: "#ff7b70"
  unobserved-soma: "#507074"
typography:
  headline:
    fontFamily: 'Vazirmatn, IRANSansX, "Noto Sans Arabic", Tahoma, sans-serif'
    fontSize: "clamp(1.35rem, 2vw, 1.55rem)"
    fontWeight: 680
    letterSpacing: "-0.02em"
  title:
    fontFamily: 'Vazirmatn, IRANSansX, "Noto Sans Arabic", Tahoma, sans-serif'
    fontSize: "1rem"
    fontWeight: 640
  label:
    fontFamily: 'Vazirmatn, IRANSansX, "Noto Sans Arabic", Tahoma, sans-serif'
    fontSize: "0.78rem"
  reading:
    fontFamily: "ui-monospace, monospace"
    fontSize: "0.76rem"
    fontWeight: 600
    lineHeight: 1.5
  code:
    fontFamily: "ui-monospace, monospace"
    fontSize: "0.65rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.08em"
rounded:
  compact-control: "8px"
  control: "12px"
  panel: "14px"
spacing:
  compact-gap: "8px"
  panel-gap: "14px"
  section-inset: "16px"
  instrument-inset: "17px"
components:
  button-primary:
    backgroundColor: "{colors.specimen-cyan}"
    textColor: "{colors.chamber-black}"
    rounded: "{rounded.control}"
  button-camera:
    backgroundColor: "{colors.chamber-black}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.control}"
    padding: "6px 12px"
  button-population:
    backgroundColor: "{colors.chamber-black}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.compact-control}"
    padding: "5px 10px"
  input-population:
    backgroundColor: "{colors.chamber-black}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.compact-control}"
    padding: "4px 8px"
    width: "4.5rem"
  input-search:
    backgroundColor: "{colors.chamber-black}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.control}"
    padding: "6px 10px"
    width: "140px"
  instrument-rail:
    backgroundColor: "{colors.optical-slate}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.panel}"
---

# FlyBrain Observatory Design

## Overview

**Creative North Star: "Living specimen chamber"**

The interface is a living specimen chamber: a large dark observation field with
a restrained scientific instrument rail. It shows measurements and motion, not
narrative claims about thought or consciousness.

The gym extends the same laboratory identity with a dimensional arena, authored
fly bodies, and measured anatomical points. Compact Persian controls and exact
monospaced readings support observation; model limitations stay available in
short disclosures.

**Key Characteristics:**

- Dark chamber and slate instruments with restrained cyan, amber, and magenta.
- Persian interface text with exact official identities and monospaced readings.
- Physical observation first, measured anatomy and training alongside it.
- Visible connection state and usable instruments when graphics are unavailable.

## Colors

The frontmatter records observed primitives. Implemented CSS tokens come from
`frontend/web/src/styles.css`; arena and soma colors come from `world-scene.ts`
and `neuron-map.ts`. The sidecar adds component previews and non-primitive metadata.
Its tonal ramps are synthesized documentation swatches, not a shipped token scale.

| Role | Token / observed treatment |
| --- | --- |
| Chamber black | `colors.chamber-black`: page, controls, and anatomical field |
| Optical slate | `colors.optical-slate`: instrument rail and population toolbar |
| Optical line | `colors.optical-line`: panel borders, dividers, and chart axes |
| Arena surface | `colors.arena-surface`: muted green floor under scene lighting |
| Specimen cyan | `colors.specimen-cyan`: primary action, selection, live state, forward output |
| Food amber | `colors.food-amber`: food, hunger, fatigue, progress, received-zero somata |
| Motor/neural magenta | `colors.motor-magenta`: turn output, association, positive neural readings |
| Paper white | `colors.paper-white`: primary text and exact readings |
| Muted cyan | `colors.muted-cyan`: labels, secondary copy, and technical captions |
| Danger | `colors.danger`: incompatible connection state |
| Unobserved soma | `colors.unobserved-soma`: measured anatomy without received activity |

Existing palette names remain unchanged; the soma legend introduces an explicit
unobserved class rather than assigning missing readings a value.

**The Reading State Rule.** Positive, received-zero, and unobserved soma points must remain distinguishable; absent activity is never rendered as a measured zero.

## Typography

The existing local Persian stack serves headings, labels, and controls. Titles
remain compact; there is no new display face. The page headline uses the
frontmatter's responsive headline role, section headings use the title role,
and scientific readings use LTR monospace. The set count is a cyan, bold
monospaced emphasis (1.6 rem, weight 700, line-height 1.2). Metadata retains its
small tracked code treatment; official labels and IDs keep their exact spelling.
No remote fonts or tracking resources are loaded.

## Layout

Desktop places the tall chamber on the right and a 330 px rail on the left.
The anatomical map occupies the rail's upper 410 px; training and the remaining
instruments scroll below it. Population setup and per-fly selection sit above
the gym scene. Exact received-neuron rows live in a disclosure below the map.
The shell uses a 76 px header, 24 px outer inset, and 14 px panel gaps. On shorter
desktop viewports (height at most 900 px), the page scrolls with two 410 px rail
rows so anatomy and training remain usable.

At 900 px and below, the order is chamber, anatomical map, then instruments.
The chamber has a 560 px minimum height and the anatomy panel is 440 px high.
At 560 px and below, the chamber minimum becomes 580 px, the page inset is 10 px,
and the instruments become one column. Population and camera controls wrap;
connection text and its dot remain visible above pause/resume. Only the small
identity code is hidden in the header.

The perspective overview fits the arena on both desktop and mobile. Fly follow
and the selected fly's approximate eye view are explicit secondary camera actions;
drag/orbit and scroll/pinch/keyboard zoom change the observer, never the fly.
The eye view is an observer camera, not biological compound-eye rendering. While
it is active, its non-interactive canvas leaves the keyboard tab order and uses
the approximation as its accessible description; overview and follow restore
the interactive canvas semantics.

Pause/resume is the single primary action. Gym population setup is the approved
secondary command; per-fly selection changes only the observation target.
Experiment 1 hides the population toolbar and training instrument. The gym
chamber has four rows: header, toolbar, growing scene, and model disclosure.
When the population form is hidden, the chamber uses three rows: header, growing
scene, and disclosure, preserving the available scene height in Experiment 1.
All browser copy, including native number-field validation, is Persian except
stable technical identities that must remain exact.

Reduced-motion preference removes position smoothing and camera damping, and
effectively suppresses CSS reveal, pulse, and transition animation. Walking and
feeding remain sampled from received simulation state; the anatomy has no
decorative spike animation or rotating neural halo.
Implemented interaction timing is 140 ms for the primary action, 650 ms for the
chamber reveal, and 2.4 s for the live-dot pulse. Primary transitions and reveal
use `cubic-bezier(0.2, 0, 0, 1)`; the pulse uses `ease-in-out`. The prior 300 ms
state timing is legacy guidance, not a currently implemented transition.

The arena has visible thickness, a muted green floor, warm directional shadows,
and a lower surrounding support plane. The gym adds a dark resistance-walking
surface with metal rollers and cyan markings. Both experiments use an enlarged,
head-forward authored skeletal fly. Each fly has its own skeleton and animation
mixer while immutable geometry and materials are shared. Walking phase follows
actual displacement; feeding follows ingestion. Pose sampling cannot move the
physical root, and retained flight clips are not played without Python flight
state. Appearance, display scale, and gait are visual synthesis, not measured
locomotor biomechanics or the MaleCNS specimen.

The current rig is the user-authorized `fly-escape` appearance asset, with source,
checksum, transformations, and permission recorded in
`frontend/web/src/assets/fly/walking-source.json`; no public redistribution
license was supplied. The former licensed female CT body retains its separate
attribution but is not the current renderer asset. Source context and model
limitations remain available in the compact model disclosure.

Model/renderer loading has its own status, independent of live instruments.
The backend badge names WebGPU or WebGL2 only after initialization. Camera
controls remain disabled until the model is ready or after a graphics failure.

The anatomical map displays 139,659 measured somata exported from the pinned
official MaleCNS annotations. The selected fly's received IDs are overlaid at
their measured coordinates: positive readings in magenta, received zero in amber,
and unobserved atlas points in muted teal. Brightness encodes the received rate,
not spikes. Missing coordinates are counted and never synthesized. Rotation and
zoom change the observer, and keyboard controls complement pointer inspection.

The received-neuron instrument binds its search directly to live telemetry,
filters the anatomical overlay, and shows exact received labels, official neuron
IDs, and activity values behind the exact-readings disclosure. Its activity count
reports positive readings against the received subset, never a whole-brain
total. The bounded scroll region retains every received record, including zero
values, and filters label or ID substrings without inventing anatomy or
activity. The measured soma total is a separate anatomical coverage count.

## Elevation & Depth

Dark tonal layers and thin optical-line borders separate instruments. The
chamber shadow is `0 18px 48px 8px rgb(0 0 0 / 28%)`; the instrument rail uses
`0 16px 44px 6px rgb(0 0 0 / 22%)`. The world gains depth from actual scene
geometry, a thick floor, and warm directional light. The flat anatomical field
uses point density and a readable received-activity overlay without invented
connections or decorative glow effects.

## Shapes

Panels retain rounded, clipped corners. Primary and camera controls share the
control radius; population fields and per-fly selection use the smaller compact
radius. The circular FB mark and status dots remain the only recurring round
interface motifs. Native meters provide narrow filled readings.

## Components

- **Primary action:** cyan fill and dark text; minimum 86 × 40 px. Hover lightens
  the fill and lifts one pixel; active state depresses it. Disabled state reduces
  opacity and retains a clear unavailable cursor.
- **Camera controls:** dark outlined buttons with cyan filled selection. Keep
  `aria-pressed`, the initialized renderer label, and the eye-view approximation.
- **Population and fly selection:** labeled native number input (integer 1–10),
  secondary apply button, wrapping per-fly buttons, and a live status. Missing,
  fractional, and out-of-range counts receive Persian validity messages. Input
  clears stale errors; pending/disconnected states disable population setup.
- **Training instrument:** cyan completed-set count, native progress meter,
  measured values, and magenta association/amber fatigue curves. A single sample
  waits for the next sample; the reward disclosure states the model limitation.
- **Neuron map and exact readings:** shared label/ID search, a three-state
  anatomical legend, missing-location count, and a native details disclosure with
  bounded semantic reading rows. Empty, no-match, and loading states stay textual.
- **Focus and connection:** buttons and the population field use visible amber
  outlines; search uses a cyan border/ring; the world canvas uses an inset cyan
  outline and the map an amber outline. Live text accompanies the status dot at
  every width. Graphics/model failure preserves live instruments and exact
  readings; anatomical failure directs the observer to the disclosure.

## Do's and Don'ts

### Do:

- **Do** preserve the dark chamber, slate instruments, and existing accent roles.
- **Do** keep Persian labels, bound field names, visible focus, and connection status at every width.
- **Do** bind animation and displayed readings to received simulation state.
- **Do** distinguish measured anatomy, received activity, and authored appearance.

### Don't:

- **Don't** invent neuron locations, connections, spikes, or missing activity values.
- **Don't** describe the authored rig, enlarged display scale, or gait as measured biomechanics.
- **Don't** let camera or fly selection steer, feed, or inject neural activity.
- **Don't** add remote fonts, tracking resources, or decorative dashboard chrome.
