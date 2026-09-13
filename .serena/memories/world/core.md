# World module
- Owns food, randomized spawn/wait/expiry state, fly body, environment geometry/physics, antenna sampling, vision samples, ingestion contact, and hunger dynamics.
- Body movement must arise only from motor drive supplied by simulation.
- Food position or hunger must never directly choose forward/turn actions.
- Hunger is continuous: 0.0 full, 1.0 starving; it rises over time and falls through ingestion.
- world must not import brain.