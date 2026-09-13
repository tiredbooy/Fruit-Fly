"""Transduction from physical fields to scalar sensory channels."""

from __future__ import annotations

from dataclasses import dataclass
import math

from simulation.signals import SensoryFrame
from world.environment import Environment
from world.fly import FlyBody


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def _wrapped_angle(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


@dataclass(frozen=True, slots=True)
class SensorRig:
    antenna_forward_offset: float = 0.32
    antenna_side_offset: float = 0.28
    visual_field_radians: float = math.pi * 0.8
    visual_distance_scale: float = 16.0

    def sample(self, environment: Environment, body: FlyBody) -> SensoryFrame:
        if environment.food is None:
            return SensoryFrame(0.0, 0.0, 0.0, 0.0)
        forward_x = math.cos(body.heading) * self.antenna_forward_offset
        forward_y = math.sin(body.heading) * self.antenna_forward_offset
        left_x = -math.sin(body.heading) * self.antenna_side_offset
        left_y = math.cos(body.heading) * self.antenna_side_offset
        smell_left = environment.odor_at(body.x + forward_x + left_x, body.y + forward_y + left_y)
        smell_right = environment.odor_at(body.x + forward_x - left_x, body.y + forward_y - left_y)

        dx = environment.food.x - body.x
        dy = environment.food.y - body.y
        distance = math.hypot(dx, dy)
        bearing = _wrapped_angle(math.atan2(dy, dx) - body.heading)
        visibility = _clamp01(1.0 - distance / self.visual_distance_scale)
        visibility *= environment.food.visual_contrast
        if abs(bearing) > self.visual_field_radians:
            visibility = 0.0
        side_bias = math.sin(bearing)
        vision_left = visibility * _clamp01(0.5 + side_bias)
        vision_right = visibility * _clamp01(0.5 - side_bias)
        return SensoryFrame(
            smell_left=_clamp01(smell_left),
            smell_right=_clamp01(smell_right),
            vision_left=_clamp01(vision_left),
            vision_right=_clamp01(vision_right),
        )
