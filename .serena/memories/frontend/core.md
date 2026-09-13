# Frontend module
- Current frontend is frontend/console.py, an animated terminal renderer.
- Text must remain English and framing/meters ASCII. The user explicitly requested the fly emoji as the only Unicode glyph; tests may inject `F` as fallback.
- Renderer consumes telemetry only and must not affect simulation state or behavior.
- Display includes world position, hunger, sensors, neuron-role activity, motor output, reward, association strength, and memory updates.
- Future Three.js/Bun frontend should consume the same telemetry boundary rather than importing world or brain internals.