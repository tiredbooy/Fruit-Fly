# Conventions
- Python uses dataclasses and explicit type hints; immutable state/value objects are preferred where practical.
- Tests mirror packages under tests/ and use stdlib unittest.
- Develop behavior with a failing test first, then minimal implementation.
- Keep world physics, brain computation, orchestration, and rendering separated.
- World exposes physical sensor samples and consumes motor drive; it never selects behavior.
- Keep terminal text English and framing/meters ASCII. The fly glyph is the explicit Unicode exception; tests may inject `F`.
- Validate persisted or external data strictly and fail with actionable errors; do not silently repair incompatible scientific data.
- Update docs/status.md after milestones and docs/science/ for scientific/model changes. Add an ADR for architectural decisions.
- Do not commit data/raw/ or data/runs/.