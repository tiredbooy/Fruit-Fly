# Simulation module
- simulation/loop.py alone orders the closed loop: sample world -> brain recall/encode -> network -> motor adapter -> body/world update -> physiology/reward -> learning -> telemetry.
- simulation/signals.py defines boundary value objects including sensory input, reward, motor drive, learning snapshot, and telemetry.
- Ingestion produces bounded RewardSignal; brain learning consumes it after current odor establishes eligibility.
- experiments/experiment_001.py composes dependencies without moving domain logic into the world.
- main.py owns CLI loading and saves memory after changed frames plus a final save.