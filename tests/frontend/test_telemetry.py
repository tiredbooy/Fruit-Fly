import json
import math
import unittest

from frontend.telemetry import (
    TelemetryProtocolError,
    frame_message,
    hello_message,
    parse_client_command,
)
from simulation.signals import (
    BodyState,
    LearningSnapshot,
    MotorDrive,
    NeuralSnapshot,
    SensoryFrame,
    TelemetryFrame,
)
from world.food import Food


class TelemetryProtocolTest(unittest.TestCase):
    def test_hello_describes_the_authoritative_simulation(self) -> None:
        message = hello_message(
            backend="full",
            dataset="male-cns:v1.0",
            fps=12.0,
            world_width=20.0,
            world_height=12.0,
        )

        self.assertEqual(
            {
                "type": "hello",
                "schema": 1,
                "backend": "full",
                "dataset": "male-cns:v1.0",
                "fps": 12.0,
                "world": {"width": 20.0, "height": 12.0},
            },
            message,
        )

    def test_frame_is_json_safe_and_sorts_active_neurons(self) -> None:
        message = frame_message(self._frame(food=Food(4.0, -2.0, radius=0.8)))

        self.assertEqual("frame", message["type"])
        self.assertEqual(7, message["step"])
        self.assertEqual({"x": 4.0, "y": -2.0, "radius": 0.8}, message["food"])
        self.assertEqual(
            [20, 10],
            [item["body_id"] for item in message["neural"]["active"]],
        )
        self.assertEqual("DNp09#20", message["neural"]["active"][0]["label"])
        json.dumps(message, allow_nan=False)

    def test_absent_food_is_encoded_as_null(self) -> None:
        self.assertIsNone(frame_message(self._frame(food=None))["food"])

    def test_non_finite_telemetry_is_rejected(self) -> None:
        frame = self._frame(food=None)
        invalid = TelemetryFrame(
            step=frame.step,
            elapsed=math.inf,
            body=frame.body,
            food=frame.food,
            hunger=frame.hunger,
            sensory=frame.sensory,
            neural=frame.neural,
            motor=frame.motor,
            ate=frame.ate,
            trail=frame.trail,
            learning=frame.learning,
        )

        with self.assertRaisesRegex(TelemetryProtocolError, "finite"):
            frame_message(invalid)

    def test_only_exact_pause_resume_command_is_accepted(self) -> None:
        self.assertFalse(
            parse_client_command('{"type":"set_running","running":false}')
        )
        self.assertTrue(
            parse_client_command('{"type":"set_running","running":true}')
        )

        invalid = (
            "not json",
            '{"type":"set_running","running":1}',
            '{"type":"set_running","running":true,"motor":1}',
            '{"type":"turn_left","running":true}',
            "x" * 1025,
        )
        for payload in invalid:
            with self.subTest(payload=payload[:40]):
                with self.assertRaises(TelemetryProtocolError):
                    parse_client_command(payload)

    def _frame(self, food: Food | None) -> TelemetryFrame:
        return TelemetryFrame(
            step=7,
            elapsed=0.7,
            body=BodyState(x=1.5, y=-0.5, heading=0.25),
            food=food,
            hunger=0.64,
            sensory=SensoryFrame(0.4, 0.2, 0.8, 0.1),
            neural=NeuralSnapshot(
                activity_by_body={10: 0.2, 20: 0.9},
                activity_by_role={"forward_left": 0.3},
                labels_by_body={10: "ORN_DM1#10", 20: "DNp09#20"},
            ),
            motor=MotorDrive(forward=0.5, turn=-0.25),
            ate=False,
            trail=((0.0, 0.0), (1.0, -0.25)),
            learning=LearningSnapshot(reward=0.0, association_strength=0.12),
        )


if __name__ == "__main__":
    unittest.main()
