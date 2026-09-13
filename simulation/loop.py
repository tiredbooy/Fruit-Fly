"""Continuous world -> sensors -> brain -> motor -> body loop."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from brain.readout import MotorReadout
from brain.sensory import BrainAdapter
from simulation.signals import RewardSignal, TelemetryFrame
from world.environment import Environment
from world.fly import FlyBody, Physiology
from world.sensors import SensorRig


@dataclass(slots=True)
class Simulation:
    environment: Environment
    body: FlyBody
    physiology: Physiology
    sensors: SensorRig
    brain: BrainAdapter
    readout: MotorReadout
    step_count: int = 0
    elapsed: float = 0.0
    _trail: list[tuple[float, float]] = field(default_factory=list)

    def step(self, dt: float) -> TelemetryFrame:
        if dt <= 0.0:
            raise ValueError("Simulation timestep must be positive")
        self.environment.advance_food(dt, self.body.x, self.body.y)
        sensory = self.sensors.sample(self.environment, self.body)
        neural = self.brain.step(sensory, self.physiology.hunger)
        motor = self.readout.decode(neural)
        self.body.apply(motor, dt)
        self.body.x, self.body.y = self.environment.constrain(self.body.x, self.body.y)

        food = self.environment.food
        distance_to_food = (
            math.hypot(food.x - self.body.x, food.y - self.body.y)
            if food is not None
            else math.inf
        )
        ate = food is not None and distance_to_food <= food.radius
        food_intake = 0.30 * dt if ate else 0.0
        self.physiology.advance(dt, food_intake)
        learning = self.brain.learn(RewardSignal(1.0 if ate else 0.0))
        if ate:
            self.environment.consume_food()

        self.step_count += 1
        self.elapsed += dt
        self._trail.append((self.body.x, self.body.y))
        if len(self._trail) > 80:
            del self._trail[:-80]
        return TelemetryFrame(
            step=self.step_count,
            elapsed=self.elapsed,
            body=self.body.state,
            food=self.environment.food,
            hunger=self.physiology.hunger,
            sensory=sensory,
            neural=neural,
            motor=motor,
            ate=ate,
            trail=tuple(self._trail),
            learning=learning,
        )
