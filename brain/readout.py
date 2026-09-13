"""Translate named descending-neuron activity into body motor drive."""

from __future__ import annotations

from dataclasses import dataclass

from simulation.signals import MotorDrive, NeuralSnapshot


@dataclass(frozen=True, slots=True)
class MotorReadout:
    forward_gain: float = 3.0
    steering_gain: float = 4.0

    def decode(self, snapshot: NeuralSnapshot) -> MotorDrive:
        roles = snapshot.activity_by_role
        forward = self.forward_gain * 0.5 * (
            roles.get("forward_left", 0.0) + roles.get("forward_right", 0.0)
        )
        left = roles.get("steering_low_left", 0.0) + roles.get("steering_high_left", 0.0)
        right = roles.get("steering_low_right", 0.0) + roles.get("steering_high_right", 0.0)
        return MotorDrive(
            forward=min(1.0, max(0.0, forward)),
            turn=min(1.0, max(-1.0, self.steering_gain * (right - left))),
        )
