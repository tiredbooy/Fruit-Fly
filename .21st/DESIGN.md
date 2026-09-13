# Project Design Context

## Project

- Name: FlyBrain Lab
- Product: scientific simulation observatory
- Stack: TypeScript, Three.js, Vite, Bun, aiohttp
- Mode: dark, compact, Persian RTL

## Source of truth

- Product constraints: `PRODUCT.md`
- Visual system: `DESIGN.md`
- Tokens and implementation: `frontend/web/src/styles.css` and
  `frontend/web/src/gym-observatory.css`
- Permanent engineering rules: `AGENTS.md`

## Required patterns

- Dominant living specimen chamber with a restrained instrument rail. The gym
  fills the right column; measured anatomy leads the left rail, training below.
  Narrow layouts stack chamber, anatomy, then instruments. Gym chambers use four
  rows (header, toolbar, growing scene, disclosure); when Experiment 1 hides the
  population form, three rows keep the scene growing between header and disclosure.
- Cyan sensory/world signals, amber food/hunger, magenta motor/neural activity.
- Semantic controls, visible focus, reduced motion, and live instruments when
  graphics fail. Keep live connection text and its dot visible on mobile.
- Native 1–10 integer population field with Persian validation and a live status;
  selected-fly buttons change only the observation target. Population setup is
  available only in gym schema 2; pause/resume remains the primary action.
- Exact official neuron IDs and labels. The rotatable soma map uses 139,659
  measured locations from the pinned MaleCNS annotations; received-positive is
  magenta, received-zero amber, and unobserved anatomy muted teal. Missing
  coordinates stay absent; rates are not rendered as spikes.
- Perspective arena overview, optional fly follow, and an approximate eye
  camera; every camera action is observer-only and never changes biological
  compound vision or simulation state.
- Eye mode removes its non-interactive canvas from the keyboard tab order and
  exposes the approximation as its accessible description; overview and follow
  restore the interactive canvas semantics.
- A bounded, scrollable live-telemetry inspector sits in the exact-readings
  disclosure below anatomy. Search filters received labels and official neuron
  IDs in both the rows and map overlay; rows preserve zero and small nonzero
  readings, and activity counts use only the received subset.
- Enlarged authored fly rig with user-authorized `fly-escape` provenance:
  independent skeletons share immutable geometry/materials; walking follows real
  displacement and feeding follows ingestion. Appearance and gait are visual
  synthesis, not measured biomechanics or the MaleCNS specimen. No flight clips
  play without Python flight state. No public redistribution license was supplied;
  the former licensed female CT body remains separately attributed.
- WebGPU preferred, actual initialized WebGL2 fallback labeled. Model and anatomy
  loading are independent of live telemetry; exact readings remain available.

## Avoid

- Frontend steering or behavior logic.
- Claims of thought, emotion, consciousness, measured authored biomechanics, or
  invented neural anatomy, connections, and spikes.
- Remote fonts, analytics, decorative gradients, and generic dashboard chrome.
