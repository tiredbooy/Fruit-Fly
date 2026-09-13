# Three.js observatory

- `main.py web` composes Experiment 1 and starts `frontend/server.py`.
- aiohttp serves `frontend/web/dist` and streams strict schema-v1 JSON on `/ws`.
- Browser commands are restricted to `{type: "set_running", running: boolean}`.
- The TypeScript client validates every server message before updating Three.js
  or the Persian RTL dashboard.
- `make web` uses compact mode; `make web-full` uses the complete MaleCNS graph.
- Three.js body and neural halo geometry is symbolic, not anatomical evidence.
- UI source lives in `frontend/web`; generated `dist` and `node_modules` are ignored.
- Visual tokens and layout rules are recorded in `DESIGN.md` and `.21st/design.json`.
