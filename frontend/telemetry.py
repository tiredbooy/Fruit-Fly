"""Strict JSON boundary between simulation telemetry and browser observers."""

from __future__ import annotations

import json
import math

from simulation.signals import TelemetryFrame


SCHEMA_VERSION = 1
MAX_CLIENT_MESSAGE_BYTES = 1_024


class TelemetryProtocolError(ValueError):
    """Raised when telemetry or a browser command violates the wire contract."""


def hello_message(
    *,
    backend: str,
    dataset: str,
    fps: float,
    world_width: float,
    world_height: float,
) -> dict[str, object]:
    message: dict[str, object] = {
        "type": "hello",
        "schema": SCHEMA_VERSION,
        "backend": backend,
        "dataset": dataset,
        "fps": fps,
        "world": {"width": world_width, "height": world_height},
    }
    _require_finite(message)
    return message


def frame_message(frame: TelemetryFrame) -> dict[str, object]:
    food = None
    if frame.food is not None:
        food = {
            "x": frame.food.x,
            "y": frame.food.y,
            "radius": frame.food.radius,
        }
    active = [
        {
            "body_id": body_id,
            "label": frame.neural.labels_by_body.get(body_id, str(body_id)),
            "activity": activity,
        }
        for body_id, activity in sorted(
            frame.neural.activity_by_body.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    message: dict[str, object] = {
        "type": "frame",
        "schema": SCHEMA_VERSION,
        "step": frame.step,
        "elapsed": frame.elapsed,
        "body": {
            "x": frame.body.x,
            "y": frame.body.y,
            "heading": frame.body.heading,
        },
        "food": food,
        "hunger": frame.hunger,
        "ate": frame.ate,
        "sensory": {
            "smell_left": frame.sensory.smell_left,
            "smell_right": frame.sensory.smell_right,
            "vision_left": frame.sensory.vision_left,
            "vision_right": frame.sensory.vision_right,
        },
        "motor": {
            "forward": frame.motor.forward,
            "turn": frame.motor.turn,
        },
        "neural": {
            "roles": dict(frame.neural.activity_by_role),
            "active": active,
        },
        "trail": [[x, y] for x, y in frame.trail],
        "learning": {
            "reward": frame.learning.reward,
            "association_strength": frame.learning.association_strength,
            "mean_eligibility": frame.learning.mean_eligibility,
            "active_kcs": frame.learning.active_kcs,
            "changed": frame.learning.changed,
        },
    }
    _require_finite(message)
    return message


def parse_client_command(text: str) -> bool:
    if len(text.encode("utf-8")) > MAX_CLIENT_MESSAGE_BYTES:
        raise TelemetryProtocolError("Client command is too large")
    try:
        document = json.loads(text)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise TelemetryProtocolError("Client command is not valid JSON") from error
    if not isinstance(document, dict):
        raise TelemetryProtocolError("Client command must be an object")
    if set(document) != {"type", "running"}:
        raise TelemetryProtocolError("Client command fields are invalid")
    if document["type"] != "set_running" or type(document["running"]) is not bool:
        raise TelemetryProtocolError("Client command values are invalid")
    return document["running"]


def _require_finite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise TelemetryProtocolError("Telemetry numbers must be finite")
    if isinstance(value, dict):
        for nested in value.values():
            _require_finite(nested)
    if isinstance(value, (list, tuple)):
        for nested in value:
            _require_finite(nested)
