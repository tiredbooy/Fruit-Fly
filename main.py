"""Command-line entry point for FlyBrain Lab development checkpoints."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import time

from brain.circuit import CircuitManifest
from brain.data import (
    DataIntegrityError,
    MaleCNSAnnotations,
    NeuronTransmitters,
    SourceManifest,
    load_release,
)
from brain.network import RuntimeCircuit
from brain.learning import LearningCircuit, LearningConfig, MushroomBodyLearning
from brain.memory import MemoryRepository, MemoryState, MemoryValidationError
from experiments.experiment_001 import create_simulation
from frontend.console import ConsoleRenderer, draw_frame, terminal_animation


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_MANIFEST = PROJECT_ROOT / "data/malecns/v1.0/source-manifest.json"
CIRCUIT_MANIFEST = PROJECT_ROOT / "data/circuits/foraging-v1.json"
RUNTIME_CIRCUIT = PROJECT_ROOT / "data/circuits/foraging-v1-runtime.json"
LEARNING_CIRCUIT = PROJECT_ROOT / "data/circuits/foraging-v1-learning.json"
RAW_DIRECTORY = PROJECT_ROOT / "data/raw/malecns/v1.0"
DEFAULT_MEMORY = PROJECT_ROOT / "data/runs/experiment-001-memory.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fruit Fly Brain Simulation Lab")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("data-status", help="Validate the official MaleCNS data")
    run = commands.add_parser("run", help="Run Experiment 1")
    run.add_argument("--animate", action="store_true", help="Show live terminal animation")
    run.add_argument("--steps", type=int, default=0, help="Number of steps; zero runs until stopped")
    run.add_argument("--fps", type=float, default=10.0, help="Frames per second")
    run.add_argument("--no-ansi", action="store_true", help="Print plain frames without terminal controls")
    run.add_argument("--seed", type=int, default=None, help="Random seed for repeatable food spawning")
    run.add_argument(
        "--memory-file",
        type=Path,
        default=DEFAULT_MEMORY,
        help="Path to persistent learned memory",
    )
    run.add_argument(
        "--reset-memory",
        action="store_true",
        help="Archive existing memory and start clean",
    )
    return parser


def data_status() -> int:
    try:
        source = SourceManifest.from_json(SOURCE_MANIFEST)
        missing = [
            source.asset_path(name, RAW_DIRECTORY)
            for name in source.sources
            if not source.asset_path(name, RAW_DIRECTORY).is_file()
        ]
        if missing:
            print("MaleCNS data is not ready:")
            for path in missing:
                print(f"- {path}")
            return 1

        print("Validating and loading MaleCNS data...")
        release = load_release(source, RAW_DIRECTORY)
        circuit = CircuitManifest.from_json(CIRCUIT_MANIFEST)
        circuit.validate(release.annotations)
        smell = circuit.resolve_sensory("food_odor", release.annotations)
        vision = circuit.resolve_sensory("grayscale_vision", release.annotations)
        runtime = RuntimeCircuit.from_json(
            RUNTIME_CIRCUIT,
            annotations=release.annotations,
            transmitters=release.transmitters,
            expected_weights_sha256=source.sources["weights"].sha256,
        )
        release.edges.require_edges(
            tuple((edge.body_pre, edge.body_post, edge.weight) for edge in runtime.edges)
        )
        learning = LearningCircuit.from_json(
            LEARNING_CIRCUIT,
            annotations=release.annotations,
            transmitters=release.transmitters,
            edges=release.edges,
            expected_weights_sha256=source.sources["weights"].sha256,
        )
    except (DataIntegrityError, ValueError, KeyError) as error:
        print(f"Data error: {error}")
        return 1

    print(f"Dataset: {source.dataset}")
    print(f"Connection rows: {release.edges.count:,}")
    print(f"ORN_DM1 olfactory neurons: {len(smell):,}")
    print(f"L1/L2 visual neurons: {len(vision):,}")
    print(f"Validated motor roles: {len(circuit.roles):,}")
    print(f"Validated runtime edges: {len(runtime.edges):,}")
    print(f"Validated learning edges: {len(learning.orn_pn_edges + learning.pn_kc_edges + learning.plastic_edges):,}")
    print(f"Official PAM01 reward neurons: {len(learning.pam01_neurons):,}")
    print("Status: data is valid and ready")
    return 0


def load_runtime_circuit() -> RuntimeCircuit:
    source = SourceManifest.from_json(SOURCE_MANIFEST)
    annotation_asset = source.sources["annotations"]
    transmitter_asset = source.sources["neurotransmitters"]
    annotations = MaleCNSAnnotations.from_feather(
        source.asset_path("annotations", RAW_DIRECTORY),
        dataset=source.dataset,
        expected_sha256=annotation_asset.sha256,
    )
    transmitters = NeuronTransmitters.from_feather(
        source.asset_path("neurotransmitters", RAW_DIRECTORY),
        expected_sha256=transmitter_asset.sha256,
    )
    manifest = CircuitManifest.from_json(CIRCUIT_MANIFEST)
    manifest.validate(annotations)
    return RuntimeCircuit.from_json(
        RUNTIME_CIRCUIT,
        annotations=annotations,
        transmitters=transmitters,
        expected_weights_sha256=source.sources["weights"].sha256,
    )


def load_experiment_brain(
    memory_path: Path,
    *,
    reset_memory: bool,
) -> tuple[RuntimeCircuit, MushroomBodyLearning, MemoryRepository, Path | None]:
    source = SourceManifest.from_json(SOURCE_MANIFEST)
    annotations = MaleCNSAnnotations.from_feather(
        source.asset_path("annotations", RAW_DIRECTORY),
        dataset=source.dataset,
        expected_sha256=source.sources["annotations"].sha256,
    )
    transmitters = NeuronTransmitters.from_feather(
        source.asset_path("neurotransmitters", RAW_DIRECTORY),
        expected_sha256=source.sources["neurotransmitters"].sha256,
    )
    runtime = RuntimeCircuit.from_json(
        RUNTIME_CIRCUIT,
        annotations=annotations,
        transmitters=transmitters,
        expected_weights_sha256=source.sources["weights"].sha256,
    )
    learning_circuit = LearningCircuit.from_json(
        LEARNING_CIRCUIT,
        annotations=annotations,
        transmitters=transmitters,
        edges=None,
        expected_weights_sha256=source.sources["weights"].sha256,
    )
    template = MemoryState.fresh(
        dataset=learning_circuit.dataset,
        weights_sha256=learning_circuit.source_weights_sha256,
        model=learning_circuit.model,
        plastic_edges=tuple(
            (edge.body_pre, edge.body_post, edge.weight)
            for edge in learning_circuit.plastic_edges
        ),
    )
    repository = MemoryRepository(memory_path)
    backup = repository.reset_with_backup() if reset_memory else None
    memory = repository.load_or_create(template)
    learner = MushroomBodyLearning(learning_circuit, memory, LearningConfig())
    return runtime, learner, repository, backup


def run_experiment(
    *,
    animate: bool,
    steps: int,
    fps: float,
    ansi: bool,
    memory_path: Path = DEFAULT_MEMORY,
    reset_memory: bool = False,
    seed: int | None = None,
) -> int:
    if fps <= 0.0:
        print("Error: frame rate must be greater than zero")
        return 2
    if steps < 0:
        print("Error: step count cannot be negative")
        return 2
    try:
        circuit, learner, repository, backup = load_experiment_brain(
            memory_path,
            reset_memory=reset_memory,
        )
    except (DataIntegrityError, MemoryValidationError, ValueError, KeyError, OSError) as error:
        print(f"Data error: {error}")
        return 1

    if backup is not None:
        print(f"Previous memory archived: {backup}")
    simulation = create_simulation(circuit, learner, seed=seed)
    dt = 1.0 / fps
    limit = steps if steps > 0 else (None if animate else 300)
    terminal_size = shutil.get_terminal_size((100, 32))
    renderer = ConsoleRenderer(
        width=min(66, max(36, terminal_size.columns - 2)),
        height=min(20, max(10, terminal_size.lines - 11)),
        ansi=ansi,
    )
    frame = None
    completed = 0
    try:
        with terminal_animation(enabled=animate and ansi):
            while limit is None or completed < limit:
                started = time.perf_counter()
                frame = simulation.step(dt)
                completed += 1
                if animate:
                    rendered = renderer.render(
                        frame,
                        simulation.environment.width,
                        simulation.environment.height,
                    )
                    draw_frame(rendered, ansi=ansi)
                if frame.learning.changed and simulation.brain.memory is not None:
                    repository.save(simulation.brain.memory)
                remaining = dt - (time.perf_counter() - started)
                if animate and remaining > 0.0:
                    time.sleep(remaining)
    except KeyboardInterrupt:
        pass
    except OSError as error:
        print(f"Memory save error: {error}")
        return 1

    try:
        if simulation.brain.memory is not None:
            repository.save(simulation.brain.memory)
    except OSError as error:
        print(f"Memory save error: {error}")
        return 1

    if frame is None:
        print("Experiment did not run")
        return 1
    if not animate:
        print(
            f"Experiment complete: {frame.step} steps, "
            f"hunger {frame.hunger:.2f}, "
            f"position ({frame.body.x:.2f}, {frame.body.y:.2f})"
        )
    elif ansi:
        print(f"Experiment stopped: {frame.step} steps")
    return 0


def main(arguments: list[str] | None = None) -> int:
    parsed = build_parser().parse_args(arguments)
    if parsed.command == "data-status":
        return data_status()
    if parsed.command == "run":
        return run_experiment(
            animate=parsed.animate,
            steps=parsed.steps,
            fps=parsed.fps,
            ansi=not parsed.no_ansi and sys.stdout.isatty(),
            memory_path=parsed.memory_file,
            reset_memory=parsed.reset_memory,
            seed=parsed.seed,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
