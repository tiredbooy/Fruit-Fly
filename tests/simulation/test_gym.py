import math
from pathlib import Path
import tempfile
import unittest

from brain.gym_circuit import load_gym_circuits
from brain.memory import MemoryValidationError
from experiments.experiment_002 import create_gym, compose_gym
from world.food import Food

ROOT = Path(__file__).resolve().parents[2]


class GymSimulationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.circuits = load_gym_circuits(ROOT)

    def make_gym(self, **options):
        return create_gym(*self.circuits, seed=7, **options)

    def test_ten_initial_flies_have_separate_alternating_equipment_contact(self):
        gym = self.make_gym(population=10)
        self.assertEqual((0, 0, 16, 8, 2),
            (gym.station.x, gym.station.y, gym.station.width, gym.station.height, gym.station.resistance))
        self.assertEqual([(-6.4, -2), (-3.2, -2), (0, -2), (3.2, -2), (6.4, -2),
                          (-6.4, 2), (-3.2, 2), (0, 2), (3.2, 2), (6.4, 2)],
                         [(round(fly.body.x, 8), fly.body.y) for fly in gym.flies])
        for index, fly in enumerate(gym.flies):
            self.assertTrue(gym.station.contains(fly.body.x, fly.body.y))
            for other in gym.flies[index + 1:]:
                self.assertGreaterEqual(math.hypot(fly.body.x - other.body.x, fly.body.y - other.body.y), 3.19)
        self.assertIsNotNone(getattr(gym, 'equipment', None))
        self.assertEqual(['bench_press', 'bicep_curl'] * 5,
                         [station.kind for station in gym.equipment.stations])
        gym.step(.1)
        self.assertEqual(10, len(gym.equipment.occupants))
        self.assertEqual(['station-1', 'station-2', 'station-3'],
                         [fly.exercise.station_id for fly in gym.flies[:3]])

    def test_population_validation_is_strict_and_readd_preserves_individual(self):
        gym = self.make_gym(population=2)
        second = gym.flies[1]
        second.brain.gym_learning.recall(smell_left=1, smell_right=1)
        second.brain.gym_learning.reinforce(.9)
        remembered = second.brain.gym_learning.memory
        for value in [True, False, 1.0, '2', None, 0, 11, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                gym.request_population(value)
        gym.request_population(1)
        self.assertEqual(2, len(gym.flies))
        gym.apply_pending_population()
        gym.request_population(2)
        gym.apply_pending_population()
        self.assertIs(second, gym.flies[1])
        self.assertEqual(remembered, second.brain.gym_learning.memory)
        self.assertEqual(0, gym.step_count)

    def test_each_fly_has_its_own_network_memory_and_physiology(self):
        gym = self.make_gym(population=2)
        first, second = gym.flies
        self.assertIs(first.brain.network.circuit, second.brain.network.circuit)
        first.brain.gym_learning.recall(smell_left=1, smell_right=1)
        first.brain.gym_learning.reinforce(.9)
        self.assertEqual(0, second.brain.gym_learning.memory.association_strength)
        self.assertEqual(0, first.brain.food_learning.memory.association_strength)
        first.physiology.hunger = 1
        self.assertEqual(.42, second.physiology.hunger)
        first.brain.network.step({next(iter(first.brain.network.circuit.sensory_inputs['gym_left'])): 1})
        self.assertTrue(all(value == 0 for value in second.brain.network._activity.values()))

    def test_real_finite_run_produces_work_learning_and_bounded_telemetry(self):
        gym = self.make_gym()
        for _ in range(300):
            frame = gym.step(.1)
        fly = frame.flies[0]
        self.assertGreater(fly.training.total_work, 0)
        self.assertGreater(fly.training.sets, 0)
        self.assertGreater(fly.training.association_strength, 0)
        self.assertEqual(0, fly.training.distance)
        self.assertEqual('station-1', fly.exercise.station_id)
        self.assertEqual(fly.training.sets, fly.exercise.completed_sets)
        self.assertEqual(300, frame.step)
        self.assertTrue(fly.frame.neural.labels_by_body)

    def test_ten_flies_remain_at_their_assigned_equipment_between_sets(self):
        gym = self.make_gym(population=10)
        assignments = {
            fly.id: (station.id, fly.body.state)
            for fly, station in zip(gym.flies, gym.equipment.stations, strict=True)
        }

        for _ in range(300):
            gym.step(.1)

        self.assertEqual(10, len(gym.equipment.occupants))
        for fly in gym.flies:
            station_id, initial_body = assignments[fly.id]
            self.assertEqual(station_id, fly.exercise.station_id)
            self.assertEqual(initial_body, fly.body.state)
            self.assertEqual(0, fly.training.distance)
            self.assertGreater(fly.training.sets, 0)

    def test_learning_disabled_retains_zero_memory(self):
        gym = self.make_gym(learning_enabled=False)
        for _ in range(300):
            gym.step(.1)
        self.assertGreater(gym.flies[0].training.sets, 0)
        self.assertEqual(0, gym.flies[0].brain.gym_learning.memory.association_strength)

    def test_each_completed_set_is_reinforced_once_even_with_a_long_tick(self):
        gym = self.make_gym()
        from brain.readout import MotorReadout
        gym.flies[0].readout = MotorReadout(steering_gain=0)
        gym.step(20)
        fly = gym.flies[0]
        self.assertGreater(fly.training.sets, 0)
        self.assertGreaterEqual(fly.exercise.repetitions, 3 * fly.training.sets)
        self.assertEqual(fly.training.sets, fly.brain.gym_learning.memory.reward_events)

    def test_coarse_steps_preserve_the_same_physics_and_rewards_as_bounded_steps(self):
        coarse, fine = self.make_gym(), self.make_gym()
        coarse.step(20)
        for _ in range(200):
            fine.step(.1)
        first, second = coarse.flies[0], fine.flies[0]
        self.assertGreater(first.exercise.repetitions, 0)
        self.assertEqual(first.exercise.repetitions, second.exercise.repetitions)
        self.assertEqual(first.training.sets, second.training.sets)
        self.assertAlmostEqual(first.training.total_work, second.training.total_work)
        self.assertAlmostEqual(first.training.fatigue, second.training.fatigue)
        self.assertAlmostEqual(first.body.x, second.body.x)
        self.assertEqual(first.brain.gym_learning.memory, second.brain.gym_learning.memory)

    def test_removing_an_active_fly_releases_its_grip_without_reward_or_clock_advance(self):
        gym = self.make_gym(population=2)
        gym.step(.1)
        second = gym.flies[1]
        self.assertEqual('station-2', second.exercise.station_id)
        position = second.body.state
        gym.request_population(1)
        gym.apply_pending_population()
        self.assertEqual(1, gym.step_count)
        self.assertIsNone(second.exercise.station_id)
        self.assertNotIn('station-2', gym.equipment.occupants)
        self.assertEqual(0, second.training.sets)
        self.assertEqual(0, second.brain.gym_learning.memory.reward_events)
        self.assertEqual(position, second.body.state)
        gym.request_population(2)
        gym.apply_pending_population()
        self.assertIs(second, gym.flies[1])
        self.assertEqual('recovery', gym.snapshot().flies[1].exercise.phase)

    def test_removing_unattached_flies_preserves_paused_free_and_recovery_state(self):
        for phase in ('free', 'recovery'):
            with self.subTest(phase=phase):
                gym = self.make_gym(population=2)
                if phase == 'recovery':
                    gym.step(.1)
                    second = gym.flies[1]
                    gym.equipment.release(second.id, second.exercise)
                before = gym.snapshot().flies[1]
                self.assertIsNone(before.exercise.station_id)
                self.assertEqual(phase, before.exercise.phase)
                if phase == 'recovery':
                    self.assertEqual(4, before.exercise.recovery_remaining)
                gym.request_population(1)
                gym.apply_pending_population()
                gym.request_population(2)
                gym.apply_pending_population()
                self.assertEqual(before, gym.snapshot().flies[1])

    def test_neural_roaming_away_from_equipment_cannot_earn_exercise_work(self):
        gym = self.make_gym()
        gym.flies[0].body.x, gym.flies[0].body.y = 8, 4
        for _ in range(10):
            frame = gym.step(.1)
        self.assertGreater(frame.flies[0].training.distance, 0)
        self.assertEqual(0, frame.flies[0].training.total_work)
        self.assertEqual(0, frame.flies[0].training.sets)
        self.assertIsNone(frame.flies[0].exercise.station_id)

    def test_supported_exercise_pose_cannot_ingest_ground_food(self):
        gym = self.make_gym()
        body = gym.flies[0].body
        gym.environment.food = Food(body.x, body.y)
        frame = gym.step(.1)
        self.assertEqual('lifting', frame.flies[0].exercise.phase)
        self.assertFalse(frame.flies[0].frame.ate)
        self.assertIsNotNone(gym.environment.food)

    def test_atomic_persistence_is_separate_and_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            gym, save = compose_gym(ROOT, path, population=2, circuits=self.circuits)
            gym.flies[1].brain.gym_learning.recall(smell_left=1, smell_right=1)
            gym.flies[1].brain.gym_learning.reinforce(.9)
            remembered = gym.flies[1].brain.gym_learning.memory
            gym.request_population(1)
            gym.apply_pending_population()
            save()
            restored, _ = compose_gym(ROOT, path, population=2, circuits=self.circuits)
            self.assertEqual(remembered, restored.flies[1].brain.gym_learning.memory)
            self.assertTrue((path / 'fly-2/food-memory.json').is_file())
            (path / 'fly-2/gym-memory.json').write_text('{invalid')
            with self.assertRaises(MemoryValidationError):
                compose_gym(ROOT, path, circuits=self.circuits)
