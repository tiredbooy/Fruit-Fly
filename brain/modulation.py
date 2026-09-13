"""Continuous internal-state modulation; no behavioral thresholds."""


def hunger_odor_gain(hunger: float) -> float:
    bounded = min(1.0, max(0.0, hunger))
    return 0.55 + 1.45 * bounded
