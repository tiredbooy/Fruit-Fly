"""Exercise actual joint motion and contact; no synthetic fly or brain objects."""

import math
import unittest

from simulation.signals import MotorDrive
from world.environment import Environment
from world.equipment import EquipmentFloor, EquipmentStation, ExerciseState
from world.fly import FlyBody
from world.gym import TrainingState


class EquipmentPhysicsTest(unittest.TestCase):
    def setUp(self):
        self.station = EquipmentStation('bench', 'bench_press', 0, 0, 0, .6, .7, .45)
        self.floor = EquipmentFloor((self.station,))
        self.environment = Environment(20, 12, None)
        self.body = FlyBody(0, 0, 0)
        self.training = TrainingState()
        self.exercise = ExerciseState()

    def advance(self, forward=1.0, dt=.01):
        self.floor.advance('fly-1', self.body, MotorDrive(forward, 0), dt,
                           self.environment, self.training, self.exercise)

    def test_zero_drive_never_creates_joint_work_reps_or_reward(self):
        for _ in range(200):
            self.advance(0, .1)
        self.assertEqual((0, 0, 0, 0), (self.exercise.joint_position,
            self.exercise.repetitions, self.training.total_work, self.training.reward))

    def test_upward_loaded_motion_earns_work_but_no_rep_until_full_return(self):
        self.advance(dt=.1)
        self.assertGreater(self.exercise.joint_position, 0)
        self.assertAlmostEqual(.42 * self.exercise.joint_position, self.training.total_work)
        self.assertEqual(0, self.exercise.repetitions)
        for _ in range(1000):
            self.advance()
            if self.exercise.phase == 'lowering':
                break
        self.assertEqual('lowering', self.exercise.phase)
        self.assertGreater(self.exercise.joint_position, .9)
        self.assertEqual(0, self.exercise.repetitions)
        for _ in range(1000):
            self.advance(0)
            if self.exercise.repetitions:
                break
        self.assertEqual(1, self.exercise.repetitions)
        self.assertEqual(0, self.training.sets)
        self.assertEqual(0, self.training.reward)

    def test_three_complete_strokes_reward_exactly_one_set_then_release(self):
        events = 0
        for _ in range(3000):
            self.advance()
            events += self.training.reward > 0
            if self.training.sets:
                break
        self.assertEqual((3, 1, 0, 1), (self.exercise.repetitions,
            self.training.sets, self.exercise.rep_in_set, events))
        self.assertAlmostEqual(1.26, self.training.total_work, places=9)
        self.assertEqual('recovery', self.exercise.phase)
        self.assertIsNone(self.exercise.station_id)
        self.assertEqual({}, self.floor.occupants)
        fatigue = self.training.fatigue
        self.assertGreater(fatigue, 0)
        self.advance(0, 4.0)
        self.assertLess(self.training.fatigue, fatigue)
        self.assertEqual(0, self.training.reward)
        self.assertEqual('free', self.exercise.phase)

    def test_continuous_training_recovers_while_gripping_then_starts_the_next_set(self):
        floor = EquipmentFloor((self.station,), continuous_training=True)
        exercise = ExerciseState()
        training = TrainingState()
        body = FlyBody(0, 0, 0)

        for _ in range(3000):
            floor.advance('fly-1', body, MotorDrive(1, 0), .01,
                          self.environment, training, exercise)
            if training.sets:
                break

        self.assertEqual({'bench': 'fly-1'}, floor.occupants)
        self.assertEqual(('bench', 'bench_press', 'recovery'),
                         (exercise.station_id, exercise.kind, exercise.phase))
        self.assertEqual((0, 0), (exercise.joint_position, exercise.rep_in_set))
        self.assertEqual((0, 0), (body.x, body.y))

        completed = (training.total_work, exercise.repetitions, training.sets)
        floor.advance('fly-1', body, MotorDrive(1, 0), 1.0,
                      self.environment, training, exercise)
        self.assertEqual(completed,
                         (training.total_work, exercise.repetitions, training.sets))
        self.assertEqual(('recovery', 0), (exercise.phase, training.reward))

        floor.advance('fly-1', body, MotorDrive(1, 0), 1.1,
                      self.environment, training, exercise)

        self.assertEqual('lifting', exercise.phase)
        self.assertGreater(exercise.joint_position, 0)
        self.assertEqual({'bench': 'fly-1'}, floor.occupants)
        self.assertEqual((0, 0), (body.x, body.y))

    def test_partial_stroke_and_return_does_not_count(self):
        self.advance(dt=.1)
        self.assertGreater(self.exercise.joint_position, 0)
        self.assertLess(self.exercise.joint_position, 1)
        self.advance(0, 3.0)
        self.assertEqual(0, self.exercise.joint_position)
        self.assertEqual(0, self.exercise.repetitions)
        self.assertEqual(0, self.training.reward)

    def test_heavier_load_reduces_displacement_for_the_same_drive(self):
        heavy = EquipmentFloor((EquipmentStation('heavy', 'bench_press', 0, 0, 0, 1.2, .7, .45),))
        heavy_state, heavy_training = ExerciseState(), TrainingState()
        self.advance(.3, .1)
        heavy.advance('fly-2', FlyBody(0, 0, 0), MotorDrive(.3, 0), .1,
                      self.environment, heavy_training, heavy_state)
        self.assertGreater(heavy_state.joint_position, 0)
        self.assertGreater(self.exercise.joint_position, heavy_state.joint_position)

    def test_contact_and_exclusive_occupancy_are_required(self):
        far_body, far_state = FlyBody(3, 3, 0), ExerciseState()
        self.floor.advance('far', far_body, MotorDrive(1, 0), .1,
                           self.environment, TrainingState(), far_state)
        self.assertIsNone(far_state.station_id)
        self.advance(dt=.1)
        other_state, other_training = ExerciseState(), TrainingState()
        self.floor.advance('other', FlyBody(0, 0, 0), MotorDrive(1, 0), .1,
                           self.environment, other_training, other_state)
        self.assertIsNone(other_state.station_id)
        self.assertEqual(0, other_training.total_work)
        self.assertEqual({'bench': 'fly-1'}, self.floor.occupants)

    def test_docking_constraint_cannot_pull_a_body_from_outside_contact(self):
        self.body.x = .46
        self.advance(0, .1)
        self.assertEqual(.46, self.body.x)
        self.assertIsNone(self.exercise.station_id)
        self.body.x = .44
        self.advance(.2, .01)
        self.assertEqual((0, 0, 0), (self.body.x, self.body.y, self.body.heading))
        self.assertEqual('bench', self.exercise.station_id)
        self.assertEqual((1.5, 0, math.pi), (self.exercise.body_elevation,
            self.exercise.body_pitch, self.exercise.body_roll))

    def test_release_racks_partial_weight_without_reward_and_contact_can_redock(self):
        self.advance(dt=.1)
        self.floor.release('fly-1', self.exercise)
        self.assertEqual({}, self.floor.occupants)
        self.assertEqual(0, self.exercise.joint_position)
        self.assertEqual(0, self.exercise.repetitions)
        self.assertIsNone(self.exercise.station_id)
        self.advance(0, 4.0)
        self.advance(.2, .01)
        self.assertEqual('bench', self.exercise.station_id)

    def test_long_timestep_preserves_stroke_boundaries_and_bounded_pose(self):
        self.advance(.4, 20.0)
        self.assertEqual(3, self.exercise.repetitions)
        self.assertEqual(1, self.training.sets)
        self.assertEqual(.9, self.training.reward)
        self.assertGreater(self.training.distance, 0)
        self.assertTrue(0 <= self.training.fatigue <= 1)
        self.assertTrue(0 <= self.exercise.joint_position <= 1)
        self.assertIsNone(self.exercise.station_id)

    def test_nonfinite_or_nonpositive_steps_leave_state_untouched(self):
        for dt in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                self.advance(dt=dt)
        self.assertEqual({}, self.floor.occupants)
        self.assertEqual(0, self.training.total_work)


if __name__ == '__main__':
    unittest.main()
