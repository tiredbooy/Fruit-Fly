"""Experiment 2 composition and per-fly persistence at the application boundary."""

from collections.abc import Callable
from pathlib import Path
import random

from brain.gym import GymBrainAdapter
from brain.gym_circuit import GymCircuits, load_gym_circuits
from brain.learning import LearningCircuit, MushroomBodyLearning
from brain.memory import MemoryRepository, MemoryState
from brain.network import ConnectomeNetwork, RuntimeCircuit
from simulation.gym import GymFly, GymSimulation, validate_population
from world.environment import Environment
from world.equipment import EquipmentFloor, EquipmentStation
from world.fly import FlyBody, Physiology
from world.food import FoodSpawnConfig, FoodSpawner


def memory_template(circuit: LearningCircuit, channel: str) -> MemoryState:
    """Bind each Experiment 2 channel to the exact official plastic edge set."""
    return MemoryState.fresh(dataset=circuit.dataset, weights_sha256=circuit.source_weights_sha256,
        model=f'experiment-002:{channel}:{circuit.model}',
        plastic_edges=tuple((e.body_pre, e.body_post, e.weight) for e in circuit.plastic_edges))


def create_gym(runtime: RuntimeCircuit, food: LearningCircuit, gym: LearningCircuit, *,
               population: int = 1, seed: int | None = None, learning_enabled: bool = True,
               memories: dict[tuple[str, str], MemoryState] | None = None) -> GymSimulation:
    """Compose one shared arena and ten bounded independent fly identities."""
    validate_population(population)
    memories = memories or {}
    bank = []
    stations = []
    for index in range(10):
        identity = f'fly-{index + 1}'
        learners = [MushroomBodyLearning(circuit, memories.get((identity, channel), memory_template(circuit, channel)))
                    for channel, circuit in (('food', food), ('gym', gym))]
        x, y, heading = -6.4 + 3.2 * (index % 5), -2.0 + 4.0 * (index // 5), .22 + .12 * index
        kind = 'bench_press' if index % 2 == 0 else 'bicep_curl'
        stations.append(EquipmentStation(f'station-{index + 1}', kind, x, y, heading,
                                        .6 if index % 2 == 0 else .4,
                                        .7 if index % 2 == 0 else .55, .45))
        # Initial contact is explicit exposure, not an inferred choice to exercise.
        bank.append(GymFly(identity, FlyBody(x, y, heading),
            Physiology(hunger=.42), GymBrainAdapter(ConnectomeNetwork(runtime), *learners, learning_enabled)))
    environment = Environment(20, 12, None, food_spawner=FoodSpawner(random.Random(seed), FoodSpawnConfig()))
    return GymSimulation(environment, tuple(bank), population,
                         equipment=EquipmentFloor(tuple(stations), continuous_training=True))


def compose_gym(root: Path, memory_directory: Path, *, population: int = 1,
                seed: int | None = None, learning_enabled: bool = True,
                brain: str = 'compact', circuits: GymCircuits | None = None) -> tuple[GymSimulation, Callable[[], None]]:
    """Load all bounded identities before starting; corrupt inactive memory also fails."""
    validate_population(population)
    if brain != 'compact':
        raise ValueError('Experiment 2 gym supports only the compact brain')
    runtime, food, gym = circuits or load_gym_circuits(root)
    repositories = {}
    memories = {}
    for index in range(1, 11):
        identity = f'fly-{index}'
        for channel, circuit in (('food', food), ('gym', gym)):
            key = identity, channel
            repositories[key] = MemoryRepository(memory_directory / identity / f'{channel}-memory.json')
            memories[key] = repositories[key].load_or_create(memory_template(circuit, channel))
    simulation = create_gym(runtime, food, gym, population=population, seed=seed,
                            learning_enabled=learning_enabled, memories=memories)

    def save() -> None:
        for fly in simulation.bank:
            repositories[fly.id, 'food'].save(fly.brain.food_learning.memory)
            repositories[fly.id, 'gym'].save(fly.brain.gym_learning.memory)

    return simulation, save
