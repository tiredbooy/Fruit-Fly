import math
import unittest

from simulation.signals import MotorDrive
from world.environment import Environment
from world.fly import FlyBody, Physiology
from world.food import Food
from world.sensors import SensorRig


class EnvironmentTest(unittest.TestCase):
    def test_absent_food_produces_no_smell_or_vision(self) -> None:
        environment = Environment(width=20.0, height=12.0, food=None)
        body = FlyBody(x=0.0, y=0.0, heading=0.0)

        frame = SensorRig().sample(environment, body)

        self.assertEqual(0.0, frame.smell_left)
        self.assertEqual(0.0, frame.smell_right)
        self.assertEqual(0.0, frame.vision_left)
        self.assertEqual(0.0, frame.vision_right)

    def test_food_is_stronger_at_the_closer_antenna(self) -> None:
        environment = Environment(width=20.0, height=12.0, food=Food(3.0, 2.0))
        body = FlyBody(x=0.0, y=0.0, heading=math.pi / 2)

        frame = SensorRig().sample(environment, body)

        self.assertGreater(frame.smell_right, frame.smell_left)
        self.assertTrue(0.0 <= frame.vision_left <= 1.0)
        self.assertTrue(0.0 <= frame.vision_right <= 1.0)

    def test_hunger_changes_continuously_and_eating_reduces_it(self) -> None:
        physiology = Physiology(hunger=0.4, metabolism_per_second=0.1)
        physiology.advance(2.0, food_intake=0.0)
        self.assertAlmostEqual(0.6, physiology.hunger)

        physiology.advance(1.0, food_intake=0.5)
        self.assertAlmostEqual(0.3, physiology.hunger)

    def test_body_motion_comes_only_from_motor_drive(self) -> None:
        body = FlyBody(x=0.0, y=0.0, heading=0.0)

        body.apply(MotorDrive(forward=1.0, turn=0.5), dt=1.0)

        self.assertGreater(body.x, 0.0)
        self.assertGreater(body.heading, 0.0)


if __name__ == "__main__":
    unittest.main()
