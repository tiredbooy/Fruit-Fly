# Project Scaffold Design

## Goal

Create the requested Python project structure without adding speculative behavior,
dependencies, or placeholder implementations.

## Structure

```text
brain/
├── __init__.py
├── data.py
├── neuron.py
├── network.py
└── sensory.py
world/
├── __init__.py
├── fly.py
├── environment.py
└── motor.py
frontend/
└── .gitkeep
data/
└── .gitkeep
main.py
```

## Responsibilities

- `brain/data.py`: load and prepare MaleCNS data.
- `brain/neuron.py`: contain the neuron domain model.
- `brain/network.py`: coordinate and run the neural network.
- `brain/sensory.py`: translate sensory input for the brain package.
- `world/fly.py`: contain the fly domain model.
- `world/environment.py`: represent the simulated environment.
- `world/motor.py`: translate network output into fly movement.
- `main.py`: serve as the future application entry point.
- `frontend/`: reserve space for the future Three.js/Bun frontend.
- `data/`: reserve space for local project datasets.

## Boundaries

`brain` and `world` are explicit Python packages. This scaffold adds no imports
between them yet, preventing premature coupling. The existing `brain/data.py`
remains unchanged.

## Error Handling

There is no runtime behavior in this change, so no error-handling policy is
introduced. Data-loading and simulation errors will be designed when those
features are implemented.

## Verification

Run Python byte-compilation and import each package/module. Confirm the existing
`brain/data.py` content is preserved and every requested path exists.
