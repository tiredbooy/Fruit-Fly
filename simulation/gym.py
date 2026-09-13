"""Authoritative multi-fly gym clock and bounded population lifecycle."""

from dataclasses import asdict, dataclass, field, replace
import math

from brain.gym import GymBrainAdapter
from brain.readout import MotorReadout
from simulation.gym_signals import ExerciseSnapshot, GymFlyFrame, GymFrame, TrainingSnapshot
from simulation.signals import LearningSnapshot, MotorDrive, NeuralSnapshot, SensoryFrame, TelemetryFrame
from world.environment import Environment
from world.equipment import EquipmentFloor, ExerciseState
from world.fly import FlyBody, Physiology
from world.gym import ResistanceStation, TrainingState, move_under_load
from world.sensors import SensorRig


def validate_population(count: object) -> int:
    """Reject coercion so bool, strings and fractional JSON counts cannot pass."""
    if type(count) is not int or not 1 <= count <= 10:
        raise ValueError('Fly count must be an integer within 1..10')
    return count


@dataclass(slots=True)
class GymFly:
    id: str
    body: FlyBody
    physiology: Physiology
    brain: GymBrainAdapter
    training: TrainingState = field(default_factory=TrainingState)
    sensors: SensorRig = field(default_factory=SensorRig)
    readout: MotorReadout = field(default_factory=MotorReadout)
    trail: list[tuple[float, float]] = field(default_factory=list)
    latest: TelemetryFrame | None = None
    exercise: ExerciseState = field(default_factory=ExerciseState)

    def advance(self, dt: float, environment: Environment, station: ResistanceStation,
                step: int, elapsed: float, equipment: EquipmentFloor | None = None) -> None:
        sensory = self.sensors.sample(environment, self.body)
        odor = equipment.sample(self.body, self.sensors) if equipment else station.sample(self.body, self.sensors)
        neural = self.brain.step(sensory, self.physiology.hunger, odor)
        motor = self.readout.decode(neural)
        previous_sets = self.training.sets
        if equipment is None:
            move_under_load(self.body, motor, dt, environment, station, self.training)
        else:
            equipment.advance(self.id, self.body, motor, dt, environment, self.training, self.exercise)
        food = environment.food
        ate = (self.exercise.station_id is None and food is not None
               and math.hypot(food.x - self.body.x, food.y - self.body.y) <= food.radius)
        self.physiology.advance(dt, .30 * dt if ate else 0.0)
        # Extra energy use is physiology, not a behavioral decision.
        self.physiology.hunger = min(1.0, self.physiology.hunger + .002 * self.training.effort * dt)
        learning = self.brain.learn(.3 if ate else 0.0, self.training.reward,
                                    self.training.sets - previous_sets)
        if ate:
            environment.consume_food()
        self.trail.append((self.body.x, self.body.y))
        del self.trail[:-80]
        self.latest = TelemetryFrame(step, elapsed, self.body.state, environment.food,
            self.physiology.hunger, sensory, neural, motor, ate, tuple(self.trail), learning)

    def snapshot(self, environment: Environment, step: int, elapsed: float) -> GymFlyFrame:
        frame = self.latest
        if frame is None:
            circuit = self.brain.network.circuit
            frame = TelemetryFrame(step, elapsed, self.body.state, environment.food,
                self.physiology.hunger, SensoryFrame(0, 0, 0, 0),
                NeuralSnapshot({n.body_id: 0.0 for n in circuit.nodes}, {r: 0.0 for r in circuit.motor_roles},
                    {n.body_id: f'{n.type or "untyped"}#{n.body_id}' for n in circuit.nodes}),
                MotorDrive(0, 0), False, (), LearningSnapshot())
        frame = replace(frame, step=step, elapsed=elapsed, food=environment.food)
        t = self.training
        return GymFlyFrame(self.id, frame, TrainingSnapshot(t.set_progress, t.sets, t.effort,
            t.fatigue, t.fitness, t.reward, self.brain.gym_learning.memory.association_strength,
            t.total_work, t.distance), ExerciseSnapshot(**asdict(self.exercise)))


class GymSimulation:
    """The bank contains at most ten stable flies, including inactive individuals."""

    def __init__(self, environment: Environment, bank: tuple[GymFly, ...], population: int,
                 station: ResistanceStation = ResistanceStation(), *,
                 equipment: EquipmentFloor | None = None) -> None:
        self.environment = environment
        self.bank = bank
        self.population = validate_population(population)
        self.station = station
        self.equipment = equipment
        self.step_count = 0
        self.elapsed = 0.0
        self._pending_population: int | None = None

    @property
    def flies(self) -> tuple[GymFly, ...]:
        return self.bank[:self.population]

    def request_population(self, count: object) -> None:
        self._pending_population = validate_population(count)

    def apply_pending_population(self) -> bool:
        if self._pending_population is None:
            return False
        if self.equipment is not None:
            for fly in self.flies[self._pending_population:]:
                if fly.exercise.station_id is not None:
                    self.equipment.release(fly.id, fly.exercise)
                    fly.training.set_progress = 0.0
                    fly.training.reward = 0.0
        self.population = self._pending_population
        self._pending_population = None
        return True

    def step(self, dt: float) -> GymFrame:
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('Gym timestep must be finite and positive')
        self.apply_pending_population()
        previous_sets = [fly.training.sets for fly in self.flies]
        start = self.elapsed
        self.step_count += 1
        self.elapsed += dt
        # Keep coarse caller ticks from freezing neural feedback across many reps.
        count = max(1, math.ceil(dt / .1 - 1e-10)) if self.equipment else 1
        interval = dt / count
        for index in range(count):
            first = self.flies[0]
            self.environment.advance_food(interval, first.body.x, first.body.y)
            elapsed = start + (index + 1) * interval
            for fly in self.flies:
                fly.advance(interval, self.environment, self.station, self.step_count, elapsed, self.equipment)
        for fly, completed_before in zip(self.flies, previous_sets, strict=True):
            fly.training.reward = .9 if fly.training.sets > completed_before else 0.0
        return self.snapshot()

    def snapshot(self) -> GymFrame:
        return GymFrame(self.step_count, self.elapsed,
            tuple(fly.snapshot(self.environment, self.step_count, self.elapsed) for fly in self.flies))
