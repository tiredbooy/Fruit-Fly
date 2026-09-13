"""Immutable gym observation values; schema-1 nested frames remain intact."""

from dataclasses import dataclass, field

from simulation.signals import TelemetryFrame


@dataclass(frozen=True, slots=True)
class TrainingSnapshot:
    set_progress: float
    sets: int
    effort: float
    fatigue: float
    fitness: float
    reward: float
    association_strength: float
    total_work: float
    distance: float


@dataclass(frozen=True, slots=True)
class ExerciseSnapshot:
    """Authoritative exercise observation; values never depend on render time."""

    station_id: str | None = None
    kind: str | None = None
    phase: str = 'free'
    joint_position: float = 0.0
    joint_velocity: float = 0.0
    repetitions: int = 0
    completed_sets: int = 0
    rep_in_set: int = 0
    recovery_remaining: float = 0.0
    body_elevation: float = 0.0
    body_pitch: float = 0.0
    body_roll: float = 0.0


@dataclass(frozen=True, slots=True)
class GymFlyFrame:
    id: str
    frame: TelemetryFrame
    training: TrainingSnapshot
    exercise: ExerciseSnapshot = field(default_factory=ExerciseSnapshot)


@dataclass(frozen=True, slots=True)
class GymFrame:
    step: int
    elapsed: float
    flies: tuple[GymFlyFrame, ...]
