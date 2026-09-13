"""One fly, one food source, hunger, smell, and simple vision."""

from __future__ import annotations

import random

from brain.learning import MushroomBodyLearning
from brain.network import ConnectomeNetwork, NeuralNetwork, RuntimeCircuit
from brain.readout import MotorReadout
from brain.sensory import BrainAdapter
from simulation.loop import Simulation
from world.environment import Environment
from world.fly import FlyBody, Physiology
from world.food import FoodSpawnConfig, FoodSpawner
from world.sensors import SensorRig


def create_simulation(
    circuit: RuntimeCircuit,
    learning: MushroomBodyLearning | None = None,
    *,
    seed: int | None = None,
    network: NeuralNetwork | None = None,
) -> Simulation:
    environment = Environment(
        width=20.0,
        height=12.0,
        food=None,
        food_spawner=FoodSpawner(
            rng=random.Random(seed),
            config=FoodSpawnConfig(),
        ),
    )
    return Simulation(
        environment=environment,
        body=FlyBody(x=-5.5, y=-2.2, heading=0.22),
        physiology=Physiology(hunger=0.42),
        sensors=SensorRig(),
        brain=BrainAdapter(network or ConnectomeNetwork(circuit), learning),
        readout=MotorReadout(),
    )
