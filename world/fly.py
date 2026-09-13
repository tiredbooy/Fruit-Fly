"""Fly body physics and internal energy state."""

from __future__ import annotations

from dataclasses import dataclass
import math

from simulation.signals import BodyState, MotorDrive


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


@dataclass(slots=True)
class Physiology:
    hunger: float = 0.35
    metabolism_per_second: float = 0.004
    digestion_efficiency: float = 0.8

    def __post_init__(self) -> None:
        self.hunger = _clamp01(self.hunger)

    def advance(self, dt: float, food_intake: float) -> None:
        self.hunger = _clamp01(
            self.hunger
            + self.metabolism_per_second * dt
            - self.digestion_efficiency * food_intake
        )


@dataclass(slots=True)
class FlyBody:
    x: float
    y: float
    heading: float
    maximum_speed: float = 3.0
    maximum_turn_rate: float = 2.8

    @property
    def state(self) -> BodyState:
        return BodyState(self.x, self.y, self.heading)

    def apply(self, drive: MotorDrive, dt: float) -> None:
        forward = _clamp01(drive.forward)
        turn = min(1.0, max(-1.0, drive.turn))
        self.heading = (self.heading + turn * self.maximum_turn_rate * dt) % (2.0 * math.pi)
        distance = forward * self.maximum_speed * dt
        self.x += math.cos(self.heading) * distance
        self.y += math.sin(self.heading) * distance
