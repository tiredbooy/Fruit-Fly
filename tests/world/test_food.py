import math
import random
import unittest

from world.food import FoodSpawnConfig, FoodSpawner


class FoodSpawnerTest(unittest.TestCase):
    def test_waits_before_spawning_food_far_from_the_fly(self) -> None:
        spawner = FoodSpawner(
            rng=random.Random(7),
            config=FoodSpawnConfig(
                minimum_spawn_delay=2.0,
                maximum_spawn_delay=2.0,
                minimum_lifetime=3.0,
                maximum_lifetime=3.0,
                inaccessible_probability=0.0,
                minimum_fly_distance=5.0,
            ),
        )

        self.assertIsNone(spawner.advance(1.0, None, 0.0, 0.0, 20.0, 12.0))
        food = spawner.advance(1.0, None, 0.0, 0.0, 20.0, 12.0)

        self.assertIsNotNone(food)
        assert food is not None
        self.assertGreaterEqual(math.hypot(food.x, food.y), 5.0)
        self.assertLessEqual(abs(food.x), 10.0 - food.radius)
        self.assertLessEqual(abs(food.y), 6.0 - food.radius)
        self.assertIsNone(spawner.advance(3.0, food, 0.0, 0.0, 20.0, 12.0))

    def test_can_spawn_food_outside_the_accessible_arena(self) -> None:
        spawner = FoodSpawner(
            rng=random.Random(11),
            config=FoodSpawnConfig(
                minimum_spawn_delay=0.0,
                maximum_spawn_delay=0.0,
                inaccessible_probability=1.0,
            ),
        )

        food = spawner.advance(0.1, None, 0.0, 0.0, 20.0, 12.0)

        self.assertIsNotNone(food)
        assert food is not None
        self.assertTrue(abs(food.x) > 10.0 or abs(food.y) > 6.0)

    def test_consumed_food_starts_a_new_waiting_period(self) -> None:
        spawner = FoodSpawner(
            rng=random.Random(5),
            config=FoodSpawnConfig(
                minimum_spawn_delay=1.0,
                maximum_spawn_delay=1.0,
            ),
        )

        spawner.consume()

        self.assertIsNone(spawner.advance(0.5, None, 0.0, 0.0, 20.0, 12.0))
        self.assertIsNotNone(spawner.advance(0.5, None, 0.0, 0.0, 20.0, 12.0))


if __name__ == "__main__":
    unittest.main()
