"""Loaded scalar joints and physical grip constraints, not a behavior policy.

All actuator, contact, pose and recovery constants are illustrative assumptions
documented in docs/science/equipment.md; none encode biological exercise roles.
"""

from dataclasses import dataclass
import math
from typing import Literal

from simulation.signals import MotorDrive
from world.environment import Environment
from world.fly import FlyBody
from world.gym import TrainingState
from world.sensors import SensorRig


EquipmentKind = Literal['bench_press', 'bicep_curl']
ExercisePhase = Literal['free', 'lifting', 'lowering', 'recovery']
MAX_PHYSICS_STEP = .01
RECOVERY_SECONDS = 4.0
CONTINUOUS_RECOVERY_SECONDS = 2.0
ACTUATOR_FORCE = 6.0
DAMPING = 3.0


@dataclass(frozen=True, slots=True)
class EquipmentStation:
    """Fixed body/grip anchor and vertical load travel in world model units."""

    id: str
    kind: EquipmentKind
    x: float
    y: float
    heading: float
    load: float
    travel: float
    grip_radius: float

    def __post_init__(self) -> None:
        if not self.id or self.kind not in ('bench_press', 'bicep_curl'):
            raise ValueError('Equipment needs an identity and supported kind')
        if not all(math.isfinite(v) for v in
                   (self.x, self.y, self.heading, self.load, self.travel, self.grip_radius)):
            raise ValueError('Equipment geometry must be finite')
        if min(self.load, self.travel, self.grip_radius) <= 0:
            raise ValueError('Equipment load, travel and grip radius must be positive')

    def odor_at(self, x: float, y: float) -> float:
        return 1.0 / (1.0 + ((x - self.x) ** 2 + (y - self.y) ** 2) / 9.0)


@dataclass(slots=True)
class ExerciseState:
    """Per-fly authoritative joint, stroke counts, grip and support pose."""

    station_id: str | None = None
    kind: EquipmentKind | None = None
    phase: ExercisePhase = 'free'
    joint_position: float = 0.0
    joint_velocity: float = 0.0
    repetitions: int = 0
    completed_sets: int = 0
    rep_in_set: int = 0
    recovery_remaining: float = 0.0
    body_elevation: float = 0.0
    body_pitch: float = 0.0
    body_roll: float = 0.0

    @property
    def set_progress(self) -> float:
        if self.station_id is None:
            return self.rep_in_set / 3.0
        stroke = self.joint_position / 2.0
        if self.phase == 'lowering':
            stroke = 1.0 - stroke
        return (self.rep_in_set + stroke) / 3.0


class EquipmentFloor:
    """Own exclusive station grips; only contact can constrain a body's pose."""

    def __init__(self, stations: tuple[EquipmentStation, ...], *,
                 continuous_training: bool = False) -> None:
        if not 1 <= len(stations) <= 10 or len({s.id for s in stations}) != len(stations):
            raise ValueError('Equipment requires 1..10 uniquely named stations')
        self.stations = stations
        self._by_id = {station.id: station for station in stations}
        self._occupants: dict[str, str] = {}
        self._continuous_training = continuous_training

    @property
    def occupants(self) -> dict[str, str]:
        return dict(self._occupants)

    def sample(self, body: FlyBody, sensors: SensorRig = SensorRig()) -> tuple[float, float]:
        """Sample the strongest physical DM2 field at each distinct antenna."""
        c, s = math.cos(body.heading), math.sin(body.heading)
        x = body.x + c * sensors.antenna_forward_offset
        y = body.y + s * sensors.antenna_forward_offset
        side = sensors.antenna_side_offset
        return (max(station.odor_at(x - s * side, y + c * side) for station in self.stations),
                max(station.odor_at(x + s * side, y - c * side) for station in self.stations))

    def release(self, fly_id: str, exercise: ExerciseState) -> None:
        """Rack a removed/released grip without counting an unfinished stroke."""
        if self._occupants.get(exercise.station_id) == fly_id:
            del self._occupants[exercise.station_id]
        exercise.station_id = None
        exercise.kind = None
        exercise.joint_position = exercise.joint_velocity = 0.0
        exercise.body_elevation = exercise.body_pitch = exercise.body_roll = 0.0
        exercise.rep_in_set = 0
        exercise.recovery_remaining = RECOVERY_SECONDS
        exercise.phase = 'recovery'

    def advance(self, fly_id: str, body: FlyBody, drive: MotorDrive, dt: float,
                environment: Environment, training: TrainingState, exercise: ExerciseState) -> None:
        """Integrate every stop crossing; time alone never creates work or reps."""
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('Equipment timestep must be finite and positive')
        count = max(1, math.ceil(dt / MAX_PHYSICS_STEP))
        step = dt / count
        previous_sets, previous_work = training.sets, training.total_work
        for _ in range(count):
            distance = work = 0.0
            if exercise.station_id is None:
                exercise.recovery_remaining = max(0.0, exercise.recovery_remaining - step)
                if exercise.recovery_remaining < 1e-9:
                    exercise.recovery_remaining = 0.0
                exercise.phase = 'recovery' if exercise.recovery_remaining else 'free'
                if exercise.phase == 'free' and drive.forward > 0:
                    self._grip(fly_id, body, exercise)
            if exercise.station_id is not None:
                station = self._by_id[exercise.station_id]
                if exercise.phase == 'recovery':
                    exercise.recovery_remaining = max(0.0, exercise.recovery_remaining - step)
                    if exercise.recovery_remaining < 1e-9:
                        exercise.recovery_remaining = 0.0
                        exercise.phase = 'lifting'
                else:
                    work = self._lift(fly_id, drive, step, station, training, exercise)
            else:
                x, y = body.x, body.y
                body.apply(MotorDrive(drive.forward * min(1.0, training.capacity), drive.turn), step)
                body.x, body.y = environment.constrain(body.x, body.y)
                distance = math.hypot(body.x - x, body.y - y)
            completed = exercise.completed_sets - training.sets
            training.advance_exercise(step, work, distance, completed, exercise.set_progress)
        training.reward = .9 if training.sets > previous_sets else 0.0
        training.effort = min(1.0, (training.total_work - previous_work) / (.6 * dt))

    def _grip(self, fly_id: str, body: FlyBody, exercise: ExerciseState) -> None:
        for station in self.stations:
            if station.id in self._occupants:
                continue
            if math.hypot(body.x - station.x, body.y - station.y) > station.grip_radius:
                continue
            # The docking support constrains only an already-contacting body.
            self._occupants[station.id] = fly_id
            body.x, body.y, body.heading = station.x, station.y, station.heading
            exercise.station_id, exercise.kind = station.id, station.kind
            exercise.phase = 'lifting'
            if station.kind == 'bench_press':
                exercise.body_elevation, exercise.body_roll = 1.5, math.pi
                exercise.body_pitch = 0.0
            else:
                exercise.body_elevation, exercise.body_pitch = .5, .55
                exercise.body_roll = 0.0
            return

    def _lift(self, fly_id: str, drive: MotorDrive, dt: float, station: EquipmentStation,
              training: TrainingState, exercise: ExerciseState) -> float:
        force = ACTUATOR_FORCE * min(1.0, max(0.0, drive.forward)) * min(1.0, training.capacity)
        if exercise.phase == 'lowering':
            force = 0.0
        acceleration = (force - station.load) / (station.load * station.travel)
        acceleration -= DAMPING * exercise.joint_velocity
        exercise.joint_velocity += acceleration * dt
        previous = exercise.joint_position
        exercise.joint_position = min(1.0, max(0.0, previous + exercise.joint_velocity * dt))
        work = station.load * station.travel * max(0.0, exercise.joint_position - previous)
        if exercise.joint_position >= 1.0:
            exercise.phase = 'lowering'
            exercise.joint_velocity = 0.0
        elif exercise.joint_position <= 0.0:
            exercise.joint_velocity = 0.0
            if exercise.phase == 'lowering':
                exercise.repetitions += 1
                exercise.rep_in_set += 1
                exercise.phase = 'lifting'
                if exercise.rep_in_set == 3:
                    exercise.completed_sets += 1
                    if self._continuous_training:
                        exercise.rep_in_set = 0
                        exercise.recovery_remaining = CONTINUOUS_RECOVERY_SECONDS
                        exercise.phase = 'recovery'
                    else:
                        self.release(fly_id, exercise)
        return work
