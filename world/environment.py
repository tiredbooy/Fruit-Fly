"""World geometry and physical fields; it contains no behavior policy."""

from __future__ import annotations

from dataclasses import dataclass
import math

from world.food import Food, FoodSpawner


@dataclass(slots=True)
class Environment:
    width: float
    height: float
    food: Food | None
    odor_length_scale: float = 4.5
    food_spawner: FoodSpawner | None = None

    def odor_at(self, x: float, y: float) -> float:
        if self.food is None:
            return 0.0
        distance = math.hypot(self.food.x - x, self.food.y - y)
        ratio = distance / self.odor_length_scale
        return self.food.odor_strength / (1.0 + ratio * ratio)

    def advance_food(self, dt: float, fly_x: float, fly_y: float) -> None:
        if self.food_spawner is None:
            return
        self.food = self.food_spawner.advance(
            dt,
            self.food,
            fly_x,
            fly_y,
            self.width,
            self.height,
        )

    def consume_food(self) -> None:
        if self.food_spawner is None:
            return
        self.food_spawner.consume()
        self.food = None

    def contains(self, x: float, y: float) -> bool:
        return abs(x) <= self.width / 2.0 and abs(y) <= self.height / 2.0

    def constrain(self, x: float, y: float) -> tuple[float, float]:
        margin = 0.05
        return (
            min(self.width / 2.0 - margin, max(-self.width / 2.0 + margin, x)),
            min(self.height / 2.0 - margin, max(-self.height / 2.0 + margin, y)),
        )
