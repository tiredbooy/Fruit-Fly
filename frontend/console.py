"""ANSI terminal visualization driven exclusively by simulation telemetry."""

from __future__ import annotations

from contextlib import contextmanager
import math
import sys
from typing import Iterator, TextIO

from simulation.signals import TelemetryFrame


RESET = "\x1b[0m"
DIM = "\x1b[2m"
GREEN = "\x1b[38;5;83m"
YELLOW = "\x1b[38;5;220m"
CYAN = "\x1b[38;5;45m"
MAGENTA = "\x1b[38;5;213m"


def _bar(value: float, width: int = 16) -> str:
    bounded = min(1.0, max(0.0, value))
    filled = round(bounded * width)
    return "#" * filled + "-" * (width - filled)


class ConsoleRenderer:
    def __init__(
        self,
        width: int = 62,
        height: int = 20,
        ansi: bool = True,
        fly_symbol: str | None = None,
        output_encoding: str | None = None,
    ) -> None:
        self.width = max(28, width)
        self.height = max(10, height)
        self.ansi = ansi
        self.fly_symbol = fly_symbol or _fly_symbol(output_encoding or sys.stdout.encoding)

    def render(self, frame: TelemetryFrame, world_width: float, world_height: float) -> str:
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

        def cell(x: float, y: float) -> tuple[int, int]:
            column = round((x / world_width + 0.5) * (self.width - 1))
            row = round((0.5 - y / world_height) * (self.height - 1))
            return (
                min(self.width - 1, max(0, column)),
                min(self.height - 1, max(0, row)),
            )

        # The field is visualized from the same inverse-square law used by Environment.
        if frame.food is not None:
            food_column, food_row = cell(frame.food.x, frame.food.y)
            for row in range(self.height):
                for column in range(self.width):
                    distance = math.hypot(column - food_column, (row - food_row) * 1.8)
                    if distance < 4.0:
                        grid[row][column] = "." if distance > 1.7 else "o"
            grid[food_row][food_column] = "O"

        for x, y in frame.trail:
            column, row = cell(x, y)
            grid[row][column] = "."
        fly_column, fly_row = cell(frame.body.x, frame.body.y)
        grid[fly_row][fly_column] = self.fly_symbol

        top = "+" + "-" * self.width + "+"
        bottom = "+" + "-" * self.width + "+"
        arena = [top, *("|" + "".join(row) + "|" for row in grid), bottom]
        roles = frame.neural.activity_by_role
        top_neurons = sorted(
            frame.neural.activity_by_body.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:4]
        active_text = "  ".join(
            f"{frame.neural.labels_by_body.get(body_id, str(body_id))} {value:.2f}"
            for body_id, value in top_neurons
            if value > 0.001
        ) or "no activity"
        status = self._status(frame, world_width, world_height)
        memory_status = " | MEMORY UPDATED" if frame.learning.changed else ""
        lines = [
            f"LIVE MALECNS BRAIN | STEP {frame.step} | TIME {frame.elapsed:5.1f}s | {status}",
            *arena,
            f"Hunger        {_bar(frame.hunger)} {frame.hunger:0.2f}",
            f"Reward        {_bar(frame.learning.reward)} {frame.learning.reward:0.2f}   Association {_bar(frame.learning.association_strength)} {frame.learning.association_strength:0.3f}{memory_status}",
            f"Smell left    {_bar(frame.sensory.smell_left)} {frame.sensory.smell_left:0.2f}   right {_bar(frame.sensory.smell_right)} {frame.sensory.smell_right:0.2f}",
            f"Vision left   {_bar(frame.sensory.vision_left)} {frame.sensory.vision_left:0.2f}   right {_bar(frame.sensory.vision_right)} {frame.sensory.vision_right:0.2f}",
            f"Forward       {_bar(frame.motor.forward)} {frame.motor.forward:0.2f}   turn {frame.motor.turn:+0.2f}",
            f"DNp09 L/R {roles.get('forward_left', 0.0):0.2f}/{roles.get('forward_right', 0.0):0.2f}   DNa01 L/R {roles.get('steering_low_left', 0.0):0.2f}/{roles.get('steering_low_right', 0.0):0.2f}   DNa02 L/R {roles.get('steering_high_left', 0.0):0.2f}/{roles.get('steering_high_right', 0.0):0.2f}",
            f"Most active neurons: {active_text}",
            self._legend(frame),
        ]
        if not self.ansi:
            return "\n".join(lines)
        colored = [
            CYAN + lines[0] + RESET,
            *lines[1 : self.height + 3],
            MAGENTA + lines[self.height + 3] + RESET,
            MAGENTA + lines[self.height + 4] + RESET,
            GREEN + lines[self.height + 5] + RESET,
            GREEN + lines[self.height + 6] + RESET,
            YELLOW + lines[self.height + 7] + RESET,
            lines[self.height + 8],
            lines[self.height + 9],
            DIM + lines[self.height + 10] + RESET,
        ]
        return "\n".join(colored)

    def _status(self, frame: TelemetryFrame, world_width: float, world_height: float) -> str:
        if frame.ate:
            return "EATING"
        if frame.food is None:
            return "WAITING FOR FOOD"
        if abs(frame.food.x) > world_width / 2.0 or abs(frame.food.y) > world_height / 2.0:
            return "FOOD OUT OF REACH"
        return "MOVING"

    def _legend(self, frame: TelemetryFrame) -> str:
        food = "   O food" if frame.food is not None else ""
        return f"Legend: {self.fly_symbol} fly{food}   . trail/odor   Ctrl+C exit"


def _fly_symbol(encoding: str | None) -> str:
    try:
        "🪰".encode(encoding or "ascii")
    except (LookupError, UnicodeEncodeError):
        return "F"
    return "🪰"


@contextmanager
def terminal_animation(stream: TextIO = sys.stdout, *, enabled: bool = True) -> Iterator[None]:
    if enabled:
        stream.write("\x1b[?1049h\x1b[?25l")
        stream.flush()
    try:
        yield
    finally:
        if enabled:
            stream.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            stream.flush()


def draw_frame(rendered: str, stream: TextIO = sys.stdout, *, ansi: bool = True) -> None:
    if ansi:
        stream.write("\x1b[H" + rendered)
    else:
        stream.write(rendered + "\n")
    stream.flush()
