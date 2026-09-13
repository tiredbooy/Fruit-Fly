import math
import unittest

from simulation.signals import MotorDrive
from world.environment import Environment
from world.fly import FlyBody
from world.gym import ResistanceStation, TrainingState, move_under_load


class GymPhysicsTest(unittest.TestCase):
    def setUp(self):
        self.station = ResistanceStation(x=-3, width=6, height=3)
        self.environment = Environment(20, 12, None)

    def test_stationary_body_never_earns_work_or_reward(self):
        body = FlyBody(-3, 0, 0)
        training = TrainingState()
        for _ in range(100):
            move_under_load(body, MotorDrive(0, 1), .1, self.environment, self.station, training)
        self.assertEqual((0, 0, 0), (training.total_work, training.sets, training.reward))

    def test_resistance_slows_actual_displacement_and_completed_work_rewards_once(self):
        body = FlyBody(-5, 0, 0)
        training = TrainingState()
        move_under_load(body, MotorDrive(1, 0), .1, self.environment, self.station, training)
        self.assertGreater(training.distance, 0)
        self.assertLess(training.distance, .3)
        for _ in range(20):
            move_under_load(body, MotorDrive(1, 0), .1, self.environment, self.station, training)
        self.assertGreater(training.sets, 0)
        self.assertGreater(training.fitness, 1)
        self.assertGreater(training.fatigue, 0)
        fatigue = training.fatigue
        move_under_load(body, MotorDrive(0, 0), .1, self.environment, self.station, training)
        self.assertEqual(0, training.reward)
        self.assertLess(training.fatigue, fatigue)

    def test_wall_contact_does_not_produce_work(self):
        body = FlyBody(9.95, 0, 0)
        training = TrainingState()
        station = ResistanceStation(x=9, width=2)
        move_under_load(body, MotorDrive(1, 0), .1, self.environment, station, training)
        self.assertEqual(0, training.total_work)

    def test_entering_lane_does_not_count_the_unloaded_entry_step_as_work(self):
        body = FlyBody(-6.1, 0, 0)
        training = TrainingState()
        move_under_load(body, MotorDrive(1, 0), .1, self.environment, self.station, training)
        self.assertGreater(body.x, -6)
        self.assertEqual(0, training.total_work)

    def test_distinct_antennae_sample_station_odor_without_food(self):
        left, right = self.station.sample(FlyBody(-3, -2, 0))
        self.assertGreater(left, right)
        self.assertGreater(right, 0)

    def test_invalid_timestep_cannot_corrupt_state(self):
        for dt in [0, -1, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                move_under_load(FlyBody(-3, 0, 0), MotorDrive(1, 0), dt,
                                self.environment, self.station, TrainingState())
