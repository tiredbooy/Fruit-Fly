import unittest

from frontend.console import ConsoleRenderer
from simulation.signals import (
    BodyState,
    LearningSnapshot,
    MotorDrive,
    NeuralSnapshot,
    SensoryFrame,
    TelemetryFrame,
)
from world.food import Food


class ConsoleRendererTest(unittest.TestCase):
    def test_frame_contains_ascii_english_live_state(self) -> None:
        telemetry = TelemetryFrame(
            step=4,
            elapsed=0.4,
            body=BodyState(0.0, 0.0, 0.0),
            food=Food(2.0, 1.0),
            hunger=0.6,
            sensory=SensoryFrame(0.2, 0.4, 0.1, 0.3),
            neural=NeuralSnapshot({}, {"forward_left": 0.5}),
            motor=MotorDrive(0.5, -0.2),
            ate=False,
            trail=((0.0, 0.0),),
            learning=LearningSnapshot(0.8, 0.25, 0.4, 5, True),
        )

        rendered = ConsoleRenderer(width=48, height=16, ansi=False, fly_symbol="F").render(
            telemetry, 20.0, 12.0
        )

        self.assertTrue(rendered.isascii())
        self.assertIn("LIVE MALECNS BRAIN", rendered)
        self.assertIn("Hunger", rendered)
        self.assertIn("O", rendered)
        self.assertIn("F", rendered)
        self.assertIn("Association", rendered)
        self.assertIn("MEMORY UPDATED", rendered)

    def test_frame_uses_fly_emoji_and_shows_when_food_is_absent(self) -> None:
        telemetry = TelemetryFrame(
            step=1,
            elapsed=0.1,
            body=BodyState(0.0, 0.0, 0.0),
            food=None,
            hunger=0.6,
            sensory=SensoryFrame(0.0, 0.0, 0.0, 0.0),
            neural=NeuralSnapshot({}, {}),
            motor=MotorDrive(0.0, 0.0),
            ate=False,
            trail=(),
        )

        rendered = ConsoleRenderer(
            width=48,
            height=16,
            ansi=False,
            fly_symbol="🪰",
        ).render(telemetry, 20.0, 12.0)

        self.assertIn("🪰", rendered)
        self.assertIn("WAITING FOR FOOD", rendered)
        self.assertNotIn("O food", rendered)

    def test_ascii_terminal_uses_safe_fly_fallback(self) -> None:
        telemetry = TelemetryFrame(
            step=1,
            elapsed=0.1,
            body=BodyState(0.0, 0.0, 0.0),
            food=None,
            hunger=0.6,
            sensory=SensoryFrame(0.0, 0.0, 0.0, 0.0),
            neural=NeuralSnapshot({}, {}),
            motor=MotorDrive(0.0, 0.0),
            ate=False,
            trail=(),
        )

        rendered = ConsoleRenderer(
            width=48,
            height=16,
            ansi=False,
            output_encoding="ascii",
        ).render(telemetry, 20.0, 12.0)

        self.assertTrue(rendered.isascii())
        self.assertIn("F fly", rendered)


if __name__ == "__main__":
    unittest.main()
