"""Physical food sources and their world-level lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random


@dataclass(frozen=True, slots=True)
class Food:
    x: float
    y: float
    odor_strength: float = 1.0
    visual_contrast: float = 1.0
    radius: float = 0.7


@dataclass(frozen=True, slots=True)
class FoodSpawnConfig:
    minimum_spawn_delay: float = 2.0
    maximum_spawn_delay: float = 8.0
    minimum_lifetime: float = 12.0
    maximum_lifetime: float = 22.0
    inaccessible_probability: float = 0.2
    minimum_fly_distance: float = 5.0
    inaccessible_margin: float = 2.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.minimum_spawn_delay <= self.maximum_spawn_delay:
            raise ValueError("food spawn delay range is invalid")
        if not 0.0 < self.minimum_lifetime <= self.maximum_lifetime:
            raise ValueError("food lifetime range is invalid")
        if not 0.0 <= self.inaccessible_probability <= 1.0:
            raise ValueError("inaccessible food probability must be within 0..1")
        if self.minimum_fly_distance < 0.0 or self.inaccessible_margin <= 0.0:
            raise ValueError("food placement distances must be non-negative")


@dataclass(slots=True)
class FoodSpawner:
    rng: random.Random
    config: FoodSpawnConfig = FoodSpawnConfig()
    _time_remaining: float = 0.0

    def __post_init__(self) -> None:
        self._schedule_wait()

    def advance(
        self,
        dt: float,
        current_food: Food | None,
        fly_x: float,
        fly_y: float,
        world_width: float,
        world_height: float,
    ) -> Food | None:
        if dt < 0.0:
            raise ValueError("food lifecycle timestep cannot be negative")
        self._time_remaining -= dt
        if self._time_remaining > 0.0:
            return current_food
        if current_food is not None:
            self._schedule_wait()
            return None
        food = self._spawn(fly_x, fly_y, world_width, world_height)
        self._time_remaining = self._duration(
            self.config.minimum_lifetime,
            self.config.maximum_lifetime,
        )
        return food

    def consume(self) -> None:
        self._schedule_wait()

    def _schedule_wait(self) -> None:
        self._time_remaining = self._duration(
            self.config.minimum_spawn_delay,
            self.config.maximum_spawn_delay,
        )

    def _duration(self, minimum: float, maximum: float) -> float:
        return self.rng.uniform(minimum, maximum)

    def _spawn(
        self,
        fly_x: float,
        fly_y: float,
        world_width: float,
        world_height: float,
    ) -> Food:
        if self.rng.random() < self.config.inaccessible_probability:
            return self._spawn_outside(world_width, world_height)
        return self._spawn_accessible(fly_x, fly_y, world_width, world_height)

    def _spawn_accessible(
        self,
        fly_x: float,
        fly_y: float,
        world_width: float,
        world_height: float,
    ) -> Food:
        half_width = max(0.0, world_width / 2.0 - 0.7)
        half_height = max(0.0, world_height / 2.0 - 0.7)
        candidates = tuple(
            Food(
                self.rng.uniform(-half_width, half_width),
                self.rng.uniform(-half_height, half_height),
            )
            for _ in range(32)
        )
        distant = tuple(
            food
            for food in candidates
            if math.hypot(food.x - fly_x, food.y - fly_y)
            >= self.config.minimum_fly_distance
        )
        return distant[0] if distant else max(
            candidates,
            key=lambda food: math.hypot(food.x - fly_x, food.y - fly_y),
        )

    def _spawn_outside(self, world_width: float, world_height: float) -> Food:
        half_width = world_width / 2.0
        half_height = world_height / 2.0
        margin = self.config.inaccessible_margin
        side = self.rng.randrange(4)
        if side < 2:
            x = (-1.0 if side == 0 else 1.0) * (half_width + margin)
            return Food(x, self.rng.uniform(-half_height, half_height))
        y = (-1.0 if side == 2 else 1.0) * (half_height + margin)
        return Food(self.rng.uniform(-half_width, half_width), y)
