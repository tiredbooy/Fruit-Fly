"""Synthetic resistance mechanics and work accounting, with no behavior policy."""

from dataclasses import dataclass
import math

from simulation.signals import MotorDrive
from world.environment import Environment
from world.fly import FlyBody
from world.sensors import SensorRig


@dataclass(frozen=True, slots=True)
class ResistanceStation:
    """A ground-plane lane with a synthetic DM2 odor field."""

    x: float = 0.0
    y: float = 0.0
    width: float = 16.0
    height: float = 8.0
    resistance: float = 2.0

    def contains(self, x: float, y: float) -> bool:
        return abs(x - self.x) <= self.width / 2 and abs(y - self.y) <= self.height / 2

    def odor_at(self, x: float, y: float) -> float:
        return 1.0 / (1.0 + ((x - self.x) ** 2 + (y - self.y) ** 2) / 9.0)

    def sample(self, body: FlyBody, sensors: SensorRig = SensorRig()) -> tuple[float, float]:
        forward_x = math.cos(body.heading) * sensors.antenna_forward_offset
        forward_y = math.sin(body.heading) * sensors.antenna_forward_offset
        left_x = -math.sin(body.heading) * sensors.antenna_side_offset
        left_y = math.cos(body.heading) * sensors.antenna_side_offset
        return (
            self.odor_at(body.x + forward_x + left_x, body.y + forward_y + left_y),
            self.odor_at(body.x + forward_x - left_x, body.y + forward_y - left_y),
        )


@dataclass(slots=True)
class TrainingState:
    """Dimensionless model physiology; accumulated work uses actual displacement."""

    set_progress: float = 0.0
    sets: int = 0
    effort: float = 0.0
    fatigue: float = 0.0
    fitness: float = 1.0
    reward: float = 0.0
    total_work: float = 0.0
    distance: float = 0.0

    @property
    def capacity(self) -> float:
        return (1.0 - .75 * self.fatigue) * self.fitness

    def advance(self, dt: float, displacement: float, load: float) -> None:
        work = displacement * load
        self.distance += displacement
        self.total_work += work
        self.effort = min(1.0, work / (3.0 * dt))
        self.fatigue = min(1.0, max(0.0, self.fatigue + dt * (.18 * self.effort - .06 * (1 - self.effort))))
        completed = int(self.total_work / 1.5)
        newly_completed = completed - self.sets
        self.reward = .9 if newly_completed > 0 else 0.0
        self.sets = completed
        self.set_progress = (self.total_work % 1.5) / 1.5
        self.fitness = min(1.5, self.fitness + .005 * newly_completed)

    def advance_exercise(self, dt: float, work: float, distance: float,
                         completed_sets: int, progress: float) -> None:
        """Account actual positive joint work and explicit full-stroke set events."""
        self.distance += distance
        self.total_work += work
        self.effort = min(1.0, work / (.6 * dt))
        self.fatigue = min(1.0, max(0.0,
            self.fatigue + .30 * work - .025 * dt * (1.0 - self.effort)))
        self.sets += completed_sets
        self.reward = .9 if completed_sets else 0.0
        self.set_progress = progress
        self.fitness = min(1.5, self.fitness + .005 * completed_sets)


def move_under_load(
    body: FlyBody, drive: MotorDrive, dt: float, environment: Environment,
    station: ResistanceStation, training: TrainingState,
) -> None:
    """Constrain motion before measuring work so walls cannot earn reward."""
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("Gym timestep must be finite and positive")
    start_x, start_y = body.x, body.y
    load = station.resistance if station.contains(start_x, start_y) else 0.0
    scaled = MotorDrive(drive.forward * min(1.0, training.capacity) / (1.0 + load), drive.turn)
    body.apply(scaled, dt)
    body.x, body.y = environment.constrain(body.x, body.y)
    distance = math.hypot(body.x - start_x, body.y - start_y)
    # A crossing step earns only the segment that actually lies inside the lane.
    fraction = _lane_fraction(start_x, start_y, body.x, body.y, station)
    training.advance(dt, distance, load * fraction)


def _lane_fraction(x0: float, y0: float, x1: float, y1: float, station: ResistanceStation) -> float:
    lower, upper = 0.0, 1.0
    for start, delta, center, size in (
        (x0, x1 - x0, station.x, station.width),
        (y0, y1 - y0, station.y, station.height),
    ):
        if delta == 0:
            if abs(start - center) > size / 2:
                return 0.0
            continue
        bounds = sorted(((center - size / 2 - start) / delta, (center + size / 2 - start) / delta))
        lower, upper = max(lower, bounds[0]), min(upper, bounds[1])
    return max(0.0, upper - lower)
