"""Small deterministic rate-neuron used on official MaleCNS edges."""

from __future__ import annotations

import math


def rate_response(current: float) -> float:
    """Bound signed synaptic current to a non-negative firing-rate proxy."""
    return math.tanh(max(0.0, current))
