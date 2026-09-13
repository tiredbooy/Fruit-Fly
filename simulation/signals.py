"""Immutable boundary values passed between world, brain, and frontend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.food import Food


@dataclass(frozen=True, slots=True)
class SensoryFrame:
    smell_left: float
    smell_right: float
    vision_left: float
    vision_right: float


@dataclass(frozen=True, slots=True)
class MotorDrive:
    forward: float
    turn: float


@dataclass(frozen=True, slots=True)
class BodyState:
    x: float
    y: float
    heading: float


@dataclass(frozen=True, slots=True)
class NeuralSnapshot:
    activity_by_body: dict[int, float]
    activity_by_role: dict[str, float]
    labels_by_body: dict[int, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RewardSignal:
    amount: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.amount <= 1.0:
            raise ValueError("reward must be within 0..1")


@dataclass(frozen=True, slots=True)
class LearningSnapshot:
    reward: float = 0.0
    association_strength: float = 0.0
    mean_eligibility: float = 0.0
    active_kcs: int = 0
    changed: bool = False


@dataclass(frozen=True, slots=True)
class TelemetryFrame:
    step: int
    elapsed: float
    body: BodyState
    food: "Food | None"
    hunger: float
    sensory: SensoryFrame
    neural: NeuralSnapshot
    motor: MotorDrive
    ate: bool
    trail: tuple[tuple[float, float], ...]
    learning: LearningSnapshot = field(default_factory=LearningSnapshot)
