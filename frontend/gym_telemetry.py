"""Gym schemas 2/3 retain unchanged schema-1 per-fly observations."""

from dataclasses import asdict
import json
from typing import Literal

from frontend.telemetry import (MAX_CLIENT_MESSAGE_BYTES, TelemetryProtocolError,
                                _require_finite, frame_message, parse_client_command)
from simulation.gym import validate_population
from simulation.gym_signals import GymFrame


def gym_frame_message(frame: GymFrame, *, schema: Literal[2, 3] = 3) -> dict[str, object]:
    """Include exercise state only for an equipment-capable schema-3 server."""
    flies = [{'id': fly.id, 'frame': frame_message(fly.frame), 'training': asdict(fly.training)}
             for fly in frame.flies]
    if schema == 3:
        for fly_message, fly in zip(flies, frame.flies, strict=True):
            fly_message['exercise'] = asdict(fly.exercise)
    message = {'type': 'gym_frame', 'schema': schema, 'step': frame.step,
               'elapsed': frame.elapsed, 'flies': flies}
    _require_finite(message)
    return message


def parse_gym_command(text: str) -> tuple[str, bool | int]:
    if len(text.encode('utf-8')) > MAX_CLIENT_MESSAGE_BYTES:
        raise TelemetryProtocolError('Client command is too large')
    try:
        document = json.loads(text)
        if isinstance(document, dict) and document.get('type') == 'set_population':
            if set(document) != {'type', 'count'}:
                raise ValueError('Invalid population fields')
            return 'population', validate_population(document['count'])
        return 'running', parse_client_command(text)
    except (ValueError, TypeError, UnicodeError) as error:
        raise TelemetryProtocolError('Invalid gym command') from error
