"""Command-line application boundary for finite and browser gym experiments."""

import argparse
import math
from pathlib import Path

from aiohttp import web

from experiments.experiment_002 import compose_gym
from frontend.gym_server import create_gym_app
from frontend.server import ObservatoryConfig
from simulation.gym import validate_population


def add_gym_commands(commands: argparse._SubParsersAction, root: Path) -> None:
    """Register gym commands without changing the Experiment 1 arguments."""
    for name in ('gym', 'gym-web'):
        parser = commands.add_parser(name, help='Run Experiment 2 resistance gym')
        parser.add_argument('--flies', type=int, default=1, help='Fly population, 1..10')
        parser.add_argument('--brain', choices=('compact', 'full'), default='compact')
        parser.add_argument('--fps', type=float, default=10.0)
        parser.add_argument('--seed', type=int, default=None)
        parser.add_argument('--no-learning', action='store_true', help='Disable cue plasticity and learned gain')
        parser.add_argument('--memory-dir', type=Path, default=root / 'data/runs/experiment-002')
        if name == 'gym':
            parser.add_argument('--steps', type=int, default=300, help='Positive finite step count')
        else:
            parser.add_argument('--host', default='127.0.0.1')
            parser.add_argument('--port', type=int, default=8000)


def run_gym(options: argparse.Namespace, root: Path) -> int:
    try:
        validate_population(options.flies)
        if options.brain != 'compact':
            raise ValueError('Experiment 2 gym supports only the compact brain')
        if not math.isfinite(options.fps) or options.fps <= 0:
            raise ValueError('Frame rate must be finite and positive')
        if options.command == 'gym' and options.steps <= 0:
            raise ValueError('Gym steps must be a positive finite count')
        if options.command == 'gym-web' and not 1 <= options.port <= 65535:
            raise ValueError('Port must be within 1..65535')
    except ValueError as error:
        print(f'Error: {error}')
        return 2
    try:
        simulation, save = compose_gym(root, options.memory_dir, population=options.flies,
            seed=options.seed, learning_enabled=not options.no_learning, brain=options.brain)
        if options.command == 'gym-web':
            app = create_gym_app(simulation=simulation,
                config=ObservatoryConfig('compact', simulation.bank[0].brain.network.circuit.dataset,
                                         options.fps, root / 'frontend/web/dist'), persist_memory=save)
            print(f'Gym observatory: http://{options.host}:{options.port}')
            web.run_app(app, host=options.host, port=options.port, print=None)
            return 0
        try:
            for _ in range(options.steps):
                simulation.step(1.0 / options.fps)
        except KeyboardInterrupt:
            pass
        finally:
            save()
        print(f'Gym complete: {simulation.step_count} steps, {simulation.population} flies, learning {"off" if options.no_learning else "on"}')
        for fly in simulation.snapshot().flies:
            t = fly.training
            print(f'{fly.id}: sets {t.sets}, work {t.total_work:.6f}, distance {t.distance:.6f}, '
                  f'fatigue {t.fatigue:.6f}, fitness {t.fitness:.6f}, gym association {t.association_strength:.6f}, '
                  f'food association {fly.frame.learning.association_strength:.6f}, hunger {fly.frame.hunger:.6f}')
        return 0
    except (ValueError, KeyError, OSError) as error:
        print(f'Gym error: {error}')
        return 1
